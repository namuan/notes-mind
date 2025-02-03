from pathlib import Path

# Embedding
EMBEDDINGS_PATH = Path.home() / ".cache" / "notechat" / "notes.db"
ST_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Credit: https://github.com/yashgoenka/chat-apple-notes
EXTRACT_SCRIPT_TO_FETCH_NOTES = """
tell application "Notes"
   repeat with eachNote in every note
      set noteId to the id of eachNote
      set noteTitle to the name of eachNote
      set noteBody to the body of eachNote
      set noteCreatedDate to the creation date of eachNote
      set noteCreated to (noteCreatedDate as «class isot» as string)
      set noteUpdatedDate to the modification date of eachNote
      set noteUpdated to (noteUpdatedDate as «class isot» as string)
      set noteContainer to container of eachNote
      set noteFolderId to the id of noteContainer
      log "{split}-id: " & noteId & "\n"
      log "{split}-created: " & noteCreated & "\n"
      log "{split}-updated: " & noteUpdated & "\n"
      log "{split}-folder: " & noteFolderId & "\n"
      log "{split}-title: " & noteTitle & "\n\n"
      log noteBody & "\n"
      log "{split}{split}" & "\n"
   end repeat
end tell
""".strip()

# Summary (Ollama)
OLLAMA_MODEL = "qwen2.5:latest"
SYSTEM_PROMPT = "You are a helpful summary generator for selected notes."
USER_PROMPT = """
You are a summarization assistant. Below is a list of notes.
Your task is to generate an accurate and concise summary that captures the key points from these notes.
Identify key supporting ideas
Highlight important facts or evidence
Reveal the author's purpose or perspective
Explore any significant implications or conclusions.

Please provide your answer strictly in valid HTML.
Do not include any markdown formatting (such as markdown quotes or code block formatting), explanations, or any text outside of the HTML.
The HTML should include appropriate tags (e.g., <html>, <head>, <body>, <h1>, <p>, <ul>, <li>) for a complete HTML document if applicable.

List of Notes:
{matching_notes}

Summary (in HTML):
""".strip()
