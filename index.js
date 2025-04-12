import Groq from "groq-sdk";

const groq = new Groq({ apiKey: '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' });

export async function main() {
  const chatCompletion = await getGroqChatCompletion();
  // Print the completion returned by the LLM.
  console.log(chatCompletion.choices[0]?.message?.content || "");
}

export async function getGroqChatCompletion() {
  return groq.chat.completions.create({
    messages: [
      {
        role: "user",
        content: "Give me 10 multiple choice questions on programming in this json format with a), b), c), d) options and the correct letter of the answer:{question1:'', question2:'' ...}",
      }
    ],
    model: "llama-3.3-70b-versatile",
    response_format: {
      type: "json_object"
    },
  });
}

await main()