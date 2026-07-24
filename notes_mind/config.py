import json
from pathlib import Path

# Embedding
EMBEDDINGS_PATH = Path.home() / ".cache" / "notechat" / "notes.db"
ST_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# JXA script to extract Apple Notes
JXA_EXTRACT_NOTES = r"""
function run(argv) {
    var Notes = Application("Notes");
    var includeLocked = argv.length > 0 && argv[0] === "true";
    var output = [];

    try {
        var accounts = Notes.accounts();
    } catch (e) {
        return JSON.stringify({error: "Could not access Notes accounts: " + e.message});
    }

    for (var ai = 0; ai < accounts.length; ai++) {
        var account = accounts[ai];
        var accountId, accountName;
        try {
            accountId = String(account.id());
            accountName = account.name() || "Unknown account";
        } catch (e) { continue; }

        var folderPaths = {};

        function visitFolder(folder, parentPath) {
            try {
                var folderId = String(folder.id());
                var folderName = folder.name() || "Unknown folder";
                var path = parentPath ? parentPath + "/" + folderName : folderName;
                folderPaths[folderId] = path;
                var children = folder.folders();
                for (var ci = 0; ci < children.length; ci++) {
                    visitFolder(children[ci], path);
                }
            } catch (e) {}
        }

        try {
            var folders = account.folders();
            for (var fi = 0; fi < folders.length; fi++) {
                visitFolder(folders[fi], "");
            }
        } catch (e) {}

        try {
            var notes = account.notes();
        } catch (e) { continue; }

        for (var ni = 0; ni < notes.length; ni++) {
            var note = notes[ni];
            try {
                var noteId = String(note.id());
                var title = note.name() || "Untitled note";

                var passwordProtected = false;
                try { passwordProtected = Boolean(note.passwordProtected()); } catch (e) {}

                if (passwordProtected && !includeLocked) continue;

                var body = "";
                try { body = String(note.plaintext()); } catch (e) {}

                var created = null;
                try {
                    var cd = note.creationDate();
                    if (cd) created = new Date(cd).toISOString();
                } catch (e) {}

                var modified = null;
                try {
                    var md = note.modificationDate();
                    if (md) modified = new Date(md).toISOString();
                } catch (e) {}

                var folderId = null;
                var folderPath = "";
                try {
                    var container = note.container();
                    folderId = String(container.id());
                    folderPath = folderPaths[folderId] || container.name() || "";
                } catch (e) {}

                output.push({
                    note_id: noteId,
                    account_id: accountId,
                    account_name: accountName,
                    title: title,
                    folder_path: folderPath,
                    created_at: created,
                    modified_at: modified,
                    password_protected: passwordProtected,
                    body: body
                });
            } catch (e) {}
        }
    }

    return JSON.stringify(output);
}
"""

# LLM (llama.cpp)
HUGGINGFACE_HUB = Path.home() / ".cache" / "huggingface" / "hub"
PREFS_FILE = Path.home() / ".cache" / "notechat" / "prefs.json"
LLM_N_CTX = 4096
LLM_N_THREADS = 4
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


def discover_gguf_models() -> list[tuple[str, str]]:
    models = []
    if not HUGGINGFACE_HUB.exists():
        return models

    for snap_dir in sorted(HUGGINGFACE_HUB.glob("models--*/snapshots/*/")):
        for gguf in sorted(snap_dir.glob("*.gguf")):
            if "mmproj" in gguf.name.lower():
                continue
            parts = snap_dir.parts
            hub_idx = parts.index("hub")
            model_dir = parts[hub_idx + 1]
            name = model_dir.replace("models--", "").replace("-GGUF", "").replace("--", "/")
            quant = gguf.stem.rsplit("-", 1)[-1] if "-" in gguf.stem else ""
            display = f"{name} ({quant})" if quant else name
            models.append((display, str(gguf)))

    return sorted(models, key=lambda x: x[0].lower())


def load_prefs() -> dict:
    if PREFS_FILE.exists():
        return json.loads(PREFS_FILE.read_text())
    return {}


def save_prefs(prefs: dict):
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREFS_FILE.write_text(json.dumps(prefs, indent=2))
