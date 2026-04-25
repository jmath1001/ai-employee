import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import tools
import actions_files
import actions_web
import actions_leads

load_dotenv()
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
chat_histories = {}


def _wants_research_doc(text: str) -> bool:
    t = (text or "").lower()
    research_words = ["search", "research", "find", "look up"]
    doc_words = ["word", "doc", "document", ".docx"]
    return any(w in t for w in research_words) and any(w in t for w in doc_words)


def ask_ai(user_input, user_id="david"):
    if user_id not in chat_histories:
        chat_histories[user_id] = [
            {"role": "system",
             "content": """You are BottyWap, a versatile AI Research & Operations Agent.

### TOOL ORDER RULES (CRITICAL — follow exactly):
1. If the user asks to search, research, find, or look something up → call deep_research FIRST.
2. Only call manage_word_doc AFTER deep_research returns real content.
3. NEVER call manage_word_doc with placeholder text like "findings will be added here" or "to be researched".
4. NEVER skip deep_research and go straight to manage_word_doc for research requests.
5. deep_research already saves a Word doc automatically — do NOT call manage_word_doc after it unless appending extra content.

### OPERATING MODES:
- RESEARCH: Use 'deep_research'. It searches the web AND saves the Word doc automatically.
- REDDIT: Use 'reddit_dive' to find community opinions.
- NEWS: Use 'aggregate_news' for multi-source news.
- TWITTER: Use 'scrape_twitter' for social sentiment.
- LEADS: Use 'find_tutoring_leads' for business contacts.

### MULTI-TASK RULE:
If the user asks for multiple things, call ALL relevant tools in the SAME response. Do not wait. Do not ask.

### STRICT RULES:
1. NEVER type JSON text. Use actual function calls.
2. Do not answer from memory for current events. SEARCH instead.
3. If a tool returns an error, report it honestly — do not write a placeholder doc."""}
        ]

    chat_histories[user_id].append({"role": "user", "content": user_input})

    if len(chat_histories[user_id]) > 20:
        chat_histories[user_id] = [chat_histories[user_id][0]] + chat_histories[user_id][-19:]

    forced_tool_retry = False
    any_tool_called = False

    while True:
        try:
            response = client.chat.completions.create(
                model="qwen2.5",
                messages=chat_histories[user_id],
                tools=tools.TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0
            )
        except Exception as e:
            return (
                "I couldn't reach the local AI model right now. "
                "Please make sure Ollama is running and try again. "
                f"Details: {e}"
            )

        msg = response.choices[0].message

        # Hallucination guard
        if not msg.tool_calls and "{" in (msg.content or ""):
            print("⚠️ Hallucination detected. Forcing retry...")
            chat_histories[user_id].append({
                "role": "user",
                "content": "ERROR: Do not type the JSON. Execute the actual function call."
            })
            continue

        chat_histories[user_id].append(msg)

        # No tool calls = final answer (unless we should force tool execution)
        if not msg.tool_calls:
            if _wants_research_doc(user_input) and not any_tool_called and not forced_tool_retry:
                forced_tool_retry = True
                chat_histories[user_id].append({
                    "role": "user",
                    "content": (
                        "SYSTEM: The user asked for web search output saved to a Word document. "
                        "You must call deep_research now. Do not ask a follow-up question."
                    )
                })
                continue
            return msg.content

        # ── Execute all tool calls in this round ──────────────────────────────
        file_signals = []   # collect FILE_SIGNALs instead of returning early
        schedule_signal = None
        research_called = False  # guard: only run deep_research once per turn

        for tool_call in msg.tool_calls:
            any_tool_called = True
            name = tool_call.function.name

            # Deduplicate heavy research tools — model sometimes batches them
            if name == "deep_research":
                if research_called:
                    print(f"\n[SKIP] {name} already ran this turn, skipping duplicate")
                    chat_histories[user_id].append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": "Skipped duplicate call. Use the result from the previous deep_research call."
                    })
                    continue
                research_called = True

            print(f"\n[!!!] TOOL: {name}")

            try:
                args = json.loads(tool_call.function.arguments)
            except:
                args = {}

            try:
                result = _run_tool(name, args, client)
            except Exception as e:
                result = f"Execution Error in {name}: {str(e)}"

            # Intercept signals — don't return yet, keep going
            if isinstance(result, str) and result.startswith("FILE_SIGNAL|"):
                file_signals.append(result)
                result = f"✅ File created: {result.split('|')[1]}"

            elif isinstance(result, str) and result.startswith("SCHEDULE_SIGNAL|"):
                schedule_signal = result
                result = "✅ Task scheduled."

            # Feed result back to AI
            chat_histories[user_id].append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": name,
                "content": str(result) if result is not None else "Tool completed with no output."
            })

        # ── After ALL tools in this round are done ────────────────────────────

        # If we collected file signals, return them all joined
        if file_signals:
            if len(file_signals) == 1:
                return file_signals[0]
            else:
                # Multiple files — return a MULTI_FILE_SIGNAL so your Telegram
                # handler can send them all
                return "MULTI_FILE_SIGNAL|" + "|".join(
                    sig.split("|")[1] for sig in file_signals
                )

        if schedule_signal:
            return schedule_signal

        # Otherwise loop — AI will see all tool results and either call more
        # tools or give a final text answer


# ── Tool dispatcher (clean separation from main loop) ────────────────────────

_PLACEHOLDER_PHRASES = [
    "will be added here",
    "to be researched",
    "research findings",
    "will be filled",
    "placeholder",
    "coming soon",
    "tbd",
]


def _run_tool(name: str, args: dict, client) -> str:
    if name == "manage_word_doc":
        content = args.get("content") or ""
        # Block placeholder content — force the AI to do real research first
        if any(phrase in content.lower() for phrase in _PLACEHOLDER_PHRASES):
            return (
                "ERROR: You wrote placeholder content. "
                "You MUST call deep_research first to get real content, "
                "then write the actual results to the document."
            )
        result = actions_files.manage_word_doc(
            args.get("filename"), args.get("title"),
            content, args.get("mode")
        )
        filename = args.get("filename") or ""
        if filename:
            if not filename.endswith(".docx"):
                filename += ".docx"
            path = os.path.join(actions_files.WORKSPACE, filename)
            if os.path.exists(path):
                return f"FILE_SIGNAL|{path}"
        return result
    elif name == "write_text_file":
        return actions_files.write_text(args.get("filename"), args.get("content"))
    elif name == "read_any_file":
        return actions_files.read_any_file(args.get("filename"))
    elif name == "list_files":
        return actions_files.list_files()
    elif name == "save_lead":
        return actions_leads.save_lead(
            args.get("center_name"), args.get("email"), args.get("city")
        )
    elif name == "clean_leads_csv":
        return actions_leads.clean_leads()
    elif name == "find_tutoring_leads":
        return actions_leads.find_tutoring_leads(args.get("city"))
    elif name == "deep_research":
        return actions_web.deep_research(args.get("query"), client)
    elif name == "reddit_dive":
        return actions_web.reddit_dive(
            args.get("query"), client, max_posts=args.get("max_posts", 5)
        )
    elif name == "aggregate_news":
        return actions_web.aggregate_news(
            args.get("query"), client, num_sources=args.get("num_sources", 3)
        )
    elif name == "scrape_twitter":
        return actions_web.scrape_twitter(
            args.get("query"), client, max_tweets=args.get("max_tweets", 30)
        )
    elif name == "send_file":
        filepath = os.path.join(
            r"C:\Users\david\my-ai-agent\bot_files",
            args.get("filename") or ""
        )
        return f"FILE_SIGNAL|{filepath}"
    elif name == "schedule_task":
        return f"SCHEDULE_SIGNAL|{args.get('minutes')}|{args.get('task_description')}"
    else:
        return f"Error: Tool '{name}' not found in registry."