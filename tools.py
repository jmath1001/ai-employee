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
            "description": "ONLY use this to create or edit a formatted Word .docx file on disk. Do NOT use this to show content to the user.",
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
            "description": "List all files currently in the workspace.",
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
            "name": "search_web",
            "description": "Searches the web for tutoring agencies or business info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hunt_email",
            "description": "Visits a website URL to find a contact email address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL of the website."}
                },
                "required": ["url"]
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
        "description": "Searches Google and visits the top 3 websites to read their actual content for detailed information.",
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
}
]