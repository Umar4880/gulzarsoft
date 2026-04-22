<tool_name>web_search</tool_name>

<description>
Executes a live search engine query to retrieve current information, news, or factual data from the public internet. Use this tool when the user's query requires up-to-date facts, external verification, or information beyond your internal training data.
</description>

<parameters>
- `query` (string, required): The exact search phrase to execute. Keep it concise and keyword-focused.
- `days_limit` (integer, optional): Restricts results to the last N days. Default is 30. Use 1 for breaking news.
</parameters>

<usage_rules>
- NEVER pass a massive, conversational sentence into the `query` parameter. Extract the core keywords.
  * BAD: "What did the CEO of OpenAI say about the new model yesterday?"
  * GOOD: "Sam Altman OpenAI new model announcement"
- If the first search returns irrelevant results, rephrase the `query` and call the tool again.
- Do NOT use this tool for basic math, coding logic, or internal system questions.
</usage_rules>