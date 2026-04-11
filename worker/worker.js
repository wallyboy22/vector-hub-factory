/**
 * Vector Hub Factory - Cloudflare Workers Proxy
 * 
 * Este worker age como proxy seguro para a API do Google Gemini.
 * Suas API keys ficam protegidas no servidor (Workers).
 * 
 * Deploy: wrangler deploy worker.js
 */

// Sua API key do Google AI Studio (configure via wrangler secret)
const GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY";

// Configuração do CORS
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Handle CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Rotas disponíveis
      if (url.pathname === "/health") {
        return new Response(JSON.stringify({ status: "ok" }), {
          headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }

      // POST /embed - Gerar embedding
      if (url.pathname === "/embed" && request.method === "POST") {
        return handleEmbed(request);
      }

      // POST /generate - Gerar resposta com LLM
      if (url.pathname === "/generate" && request.method === "POST") {
        return handleGenerate(request);
      }

      // 404
      return new Response("Not Found", { status: 404 });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }
  },
};

async function handleEmbed(request) {
  const body = await request.json();
  const { text, model = "gemini-embedding-001" } = body;

  if (!text) {
    return new Response(JSON.stringify({ error: "Text is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  // Chamar Google AI Studio API
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:embedContent?key=${GOOGLE_API_KEY}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: { parts: [{ text }] },
        taskType: "RETRIEVAL_QUERY",
      }),
    }
  );

  const data = await response.json();
  
  return new Response(JSON.stringify(data), {
    headers: { "Content-Type": "application/json", ...corsHeaders },
  });
}

async function handleGenerate(request) {
  const body = await request.json();
  const { prompt, model = "gemini-2.0-flash-001", temperature = 0.1 } = body;

  if (!prompt) {
    return new Response(JSON.stringify({ error: "Prompt is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  // Chamar Google AI Studio API (Google AI SDK)
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${GOOGLE_API_KEY}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          temperature,
          topP: 0.95,
          topK: 40,
          maxOutputTokens: 8192,
        },
        systemInstruction: {
          parts: [{ text: "Você é um assistente científico do MapBiomas. Responda em português brasileiro." }],
        },
      }),
    }
  );

  const data = await response.json();
  
  // Extrair texto da resposta
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || "";
  
  return new Response(JSON.stringify({ text }), {
    headers: { "Content-Type": "application/json", ...corsHeaders },
  });
}