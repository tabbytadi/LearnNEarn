import OpenAI from 'openai';
const openai = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: "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",
});
async function main() {
  const completion = await openai.chat.completions.create({
    model: "deepseek/deepseek-r1-zero:free",
    messages: [
      {
        "role": "user",
        "content": "Generate me a history test with multiple choices for 4th grade. Create 3 questions"
      }
    ],

  });

  console.log(completion.choices[0].message.content);
}

await main();