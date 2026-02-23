import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import tools  # The Menu
import actions_files  # The Muscles
import actions_web
import actions_leads
import httpx

load_dotenv()
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
chat_histories = {}


def ask_ai(user_input, user_id="david"):
    if user_id not in chat_histories:
        chat_histories[user_id] = [
            {"role": "system",
             "content": """You are a lead generation assistant. When asked to find tutoring leads, you MUST use the find_tutoring_leads tool. 
             NEVER make up emails or business information. 
             If a tool fails, say it failed and try again. Do not answer from memory.
             "CRITICAL: You are a function-calling assistant. NEVER write out JSON tool calls as text. 
             NEVER print tool names as text. 
             ALWAYS use the actual tool calling mechanism. 
             If you need to use find_tutoring_leads, actually call it - do not type it out."
             """}
        ]

    chat_histories[user_id].append({"role": "user", "content": user_input})

    # Keep memory from getting too huge
    if len(chat_histories[user_id]) > 20:
        chat_histories[user_id] = [chat_histories[user_id][0]] + chat_histories[user_id][-19:]

    while True:
        response = client.chat.completions.create(
            model="llama3.1",
            messages=chat_histories[user_id],
            tools=tools.TOOL_SCHEMAS,
            tool_choice="auto"
        )

        msg = response.choices[0].message
        chat_histories[user_id].append(msg)

        if not msg.tool_calls:
            return msg.content

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # --- Handle tools safely ---
            try:
                if name == "manage_word_doc":
                    result = actions_files.manage_word_doc(
                        args.get("filename"), args.get("title"), args.get("content"), args.get("mode")
                    )
                elif name == "write_text_file":
                    result = actions_files.write_text(args.get("filename"), args.get("content"))
                elif name == "read_any_file":
                    result = actions_files.read_any_file(args.get("filename"))
                elif name == "deep_research":
                    result = actions_web.deep_research(args.get("query"), client)
                elif name == "search_web":
                    result = actions_web.search_web(args.get("query"))
                elif name == "find_tutoring_leads":
                    result = actions_leads.find_tutoring_leads(args.get("city"))
                elif name == "list_files":
                    result = actions_files.list_files()
                elif name == "hunt_email":
                    result = actions_web.hunt_email(args.get("url"))
                elif name == "save_lead":
                    result = actions_leads.save_lead(
                        args.get("center_name"),
                        args.get("email"),
                        args.get("city")
                    )
                elif name == "send_file":
                    filepath = os.path.join(r"C:\Users\david\my-ai-agent\bot_files", args.get("filename"))
                    chat_histories[user_id].append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": "Sending file to Telegram."
                    })
                    return f"FILE_SIGNAL|{filepath}"
                elif name == "schedule_task":
                    chat_histories[user_id].append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": "Task successfully scheduled."
                    })
                    return f"SCHEDULE_SIGNAL|{args.get('minutes')}|{args.get('task_description')}"
                else:
                    result = "Tool not found."
            except Exception as e:
                # CRITICAL: always return a string for OpenAI
                result = f"Tool {name} failed with error: {e}"

            # --- Append the tool result ---
            chat_histories[user_id].append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": name,
                "content": result
            })