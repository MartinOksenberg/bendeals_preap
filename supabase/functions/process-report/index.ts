import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

// This is the URL of your deployed Python FastAPI server.
// You MUST set this in the Supabase Edge Function settings.
const PYTHON_API_URL = Deno.env.get('PYTHON_API_URL')
// This is the bucket where your credit reports are stored.
const STORAGE_BUCKET = 'credit-reports'

// Standard CORS headers for browser-based calls.
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle preflight OPTIONS request for CORS.
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // 1. Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    )

    // 2. Get the application record from the request body.
    // This function is intended to be called by a database webhook/trigger.
    const { record: application } = await req.json()
    if (!application || !application.id || !application.business_credit_report_file_path) {
      throw new Error('Invalid application record provided in the request body.')
    }
    console.log(`Processing application ID: ${application.id}`)

    // 3. Create a signed URL for the PDF file in Supabase Storage.
    const filePath = application.business_credit_report_file_path
    const { data: signedUrlData, error: signedUrlError } = await supabaseClient
      .storage
      .from(STORAGE_BUCKET)
      .createSignedUrl(filePath, 3600) // The URL will be valid for 1 hour (3600 seconds)

    if (signedUrlError) throw signedUrlError
    console.log('Successfully created signed URL for the report.')

    // 4. Call the Python backend service to process the report.
    if (!PYTHON_API_URL) throw new Error('PYTHON_API_URL is not set in environment variables.')

    const pythonResponse = await fetch(PYTHON_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_url: signedUrlData.signedUrl }),
    })

    if (!pythonResponse.ok) {
      const errorBody = await pythonResponse.text()
      throw new Error(`Python API Error (${pythonResponse.status}): ${errorBody}`)
    }
    
    const analysis = await pythonResponse.json()
    console.log(`Received analysis from Python API. Risk bracket: ${analysis.risk_bracket}`)

    // 5. Determine the new status based on the risk bracket.
    let newStatus = 'review_needed' // Default status
    const bracket = analysis.risk_bracket?.toLowerCase() || ''
    if (bracket.includes('rejected') || bracket.includes('0') || bracket.includes('15,000')) {
      newStatus = 'rejected'
    } else if (bracket.includes('approved') || bracket.includes('100,000') || bracket.includes('50,000')) {
      newStatus = 'approved'
    }

    // 6. Update the application in the database with the results.
    const { error: updateError } = await supabaseClient
      .from('applications')
      .update({
        analysis_result: analysis.analysis_result,
        risk_bracket: analysis.risk_bracket,
        analysis_explanation: analysis.analysis_explanation,
        extracted_data: analysis.extracted_data,
        analysis_completed_at: analysis.analysis_completed_at,
        status: newStatus,
      })
      .eq('id', application.id)

    if (updateError) throw updateError
    console.log(`Successfully updated application ${application.id} with status '${newStatus}'.`)

    return new Response(JSON.stringify({ success: true, applicationId: application.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })
  } catch (error) {
    console.error('Error processing application:', error)
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500,
    })
  }
}) 