import actions_files

# This file now acts as the 'Menu' for OpenAI and the 'Router' for brain.py

TOOL_SCHEMAS = [
    # --- TEXT FILE TOOLS ---
    {
        "type": "function",
        "function": {
            "name": "write_text_file",
            "description": "ONLY use this to save raw plain text to a .txt file on disk. Do NOT use this to show content to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["filename", "content"]
            }
        }
    },
    # --- WORD DOCUMENT TOOLS ---
    {
        "type": "function",
        "function": {
            "name": "manage_word_doc",
            "description": "Write KNOWN content to a Word doc. NEVER use this with placeholder text. NEVER call this before deep_research for research requests — deep_research already creates its own Word doc automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "title": {"type": "string", "description": "The big heading for new docs"},
                    "content": {"type": "string", "description": "The text to write or add"},
                    "mode": {"type": "string", "enum": ["create", "append"], "description": "'create' for new docs, 'append' to add to existing ones"}
                },
                "required": ["filename", "content", "mode"]
            }
        }
    },
    # --- GENERAL TOOLS ---
    {
        "type": "function",
        "function": {
            "name": "read_any_file",
            "description": "Read content from any file (.txt or .docx).",
            "parameters": {
                "type": "object",
                "properties": {"filename": {"type": "string"}},
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files currently in the workspace. If the prompt asks for what files are in the directory or what files in workspace, this should be used.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_task",
            "description": "Schedule a task for the future.",
            "parameters": {
                "type": "object",
                "properties": {
                    "minutes": {"type": "number"},
                    "task_description": {"type": "string"}
                },
                "required": ["minutes", "task_description"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "save_lead",
            "description": "Saves a center's name, email, and city to a CSV file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "center_name": {"type": "string"},
                    "email": {"type": "string"},
                    "city": {"type": "string"}
                },
                "required": ["center_name", "email", "city"]
            }
        }
    },

{
    "type": "function",
    "function": {
        "name": "deep_research",
        "description": "Primary web research tool. Use this whenever the user asks to search/find/research a topic, especially if they ask for a Word document output.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The research topic or question."}
            },
            "required": ["query"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "find_tutoring_leads",
        "description": "Searches for tutoring agencies in a city, visits their websites, finds contact emails, and saves them as leads.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city to search in"}
            },
            "required": ["city"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "send_file",
        "description": "ONLY use this when the user explicitly asks to RECEIVE or be SENT a file in Telegram. Use this after a file has been created.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The filename to send"}
            },
            "required": ["filename"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "clean_leads_csv",
        "description": "Cleans the leads.csv file. It removes duplicates, validates email formats, and filters out rows containing specific 'junk' keywords (like 'sentry', 'select', or 'v2.9.0').",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the CSV file to clean (default: leads.csv)"
                },
                "junk_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of strings that, if found in an email, should cause the row to be deleted (e.g. ['sentry', 'v2.9.0', 'ingest'])."
                }
            },
            "required": []
        }
    }
},
# ADD THESE 3 ENTRIES to your TOOL_SCHEMAS list in tools.py

{
    "type": "function",
    "function": {
        "name": "reddit_dive",
        "description": "Searches Reddit for a topic, dives into threads, reads real comments, and saves a Word doc with community opinions and debates.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The topic to search Reddit for"},
                "max_posts": {"type": "integer", "description": "How many threads to read (default: 5)"}
            },
            "required": ["query"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "aggregate_news",
        "description": "Searches multiple news sources (BBC, Reuters, AP, Guardian, Al Jazeera) for a topic, compares coverage, and saves a balanced Word doc report.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The news topic to research"},
                "num_sources": {"type": "integer", "description": "How many sources to check (default: 3, max: 5)"}
            },
            "required": ["query"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "scrape_twitter",
        "description": "Scrapes Twitter/X via Nitter (no login needed) for a topic or hashtag, analyzes sentiment and opinions, and saves a Word doc.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The topic, hashtag, or keyword to search on Twitter"},
                "max_tweets": {"type": "integer", "description": "Max tweets to collect (default: 30)"}
            },
            "required": ["query"]
        }
    }
},
]