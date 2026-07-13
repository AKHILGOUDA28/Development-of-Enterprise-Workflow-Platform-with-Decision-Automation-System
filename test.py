"""
test.py
-------
Command-line interface to test the AI Agent system.

Run with:  python test.py

Menu:
  1 - Ask a question  (runs all 4 agents via LangGraph workflow)
  2 - View conversation history  (short-term memory)
  3 - Save a note  (long-term memory)
  4 - View saved notes  (long-term memory)
  5 - Run a sample question
  0 - Exit
"""

from workflow import run_workflow
from memory import short_memory, long_memory


# --------------------------------------------------
# Display helpers
# --------------------------------------------------
def divider(title=""):
    print("\n" + "=" * 58)
    if title:
        print(f"  {title}")
        print("=" * 58)


# --------------------------------------------------
# Menu actions
# --------------------------------------------------
def ask_question():
    query = input("\n  Enter your question: ").strip()
    if not query:
        print("  Please enter a question.")
        return

    print("\n  Running agents — please wait...")
    print("  Planner → Researcher → Decision → Executor\n")

    result = run_workflow(query)

    # Save to short-term memory
    short_memory.add("user",  query)
    short_memory.add("agent", result["answer"])

    divider("STEP 1 — PLANNER AGENT")
    print(result["plan"])

    divider("STEP 2 — RESEARCHER AGENT")
    print(result["research"])

    divider("STEP 3 — DECISION AGENT")
    print(result["decision"])

    divider("STEP 4 — EXECUTOR AGENT  (Final Answer)")
    print(result["answer"])
    divider()


def view_history():
    history = short_memory.get()
    divider("Conversation History  (Short-Term Memory)")
    if not history:
        print("  No history yet.")
    else:
        for i, item in enumerate(history, 1):
            role = item["role"].upper()
            msg  = item["message"]
            # Truncate long messages for display
            preview = msg[:150] + ("..." if len(msg) > 150 else "")
            print(f"\n  [{i}] {role}:\n  {preview}")
    divider()


def save_note():
    key   = input("\n  Label (e.g. company_name): ").strip()
    value = input("  Note: ").strip()
    if key and value:
        long_memory.save(key, value)
        print(f"\n  Saved → {key}: {value}")
    else:
        print("  Both label and note are required.")


def view_notes():
    notes = long_memory.show_all()
    divider("Saved Notes  (Long-Term Memory)")
    if not notes:
        print("  No notes saved yet.")
    else:
        for key, val in notes.items():
            print(f"  {key}: {val}")
    divider()


def run_sample():
    query = "How can a retail company use AI to reduce customer churn?"
    print(f"\n  Sample question:\n  \"{query}\"")
    print("\n  Running agents — please wait...")
    print("  Planner → Researcher → Decision → Executor\n")

    result = run_workflow(query)
    short_memory.add("user",  query)
    short_memory.add("agent", result["answer"])

    divider("FINAL ANSWER  (Executor Agent)")
    print(result["answer"])
    divider()


# --------------------------------------------------
# Main menu
# --------------------------------------------------
MENU = """
╔══════════════════════════════════════════════════════╗
║     AI Agent Coordination & Decision Engine          ║
║     Interactive Testing Dashboard                    ║
╠══════════════════════════════════════════════════════╣
║   1.  Ask a question                                 ║
║   2.  View conversation history                      ║
║   3.  Save a note to memory                          ║
║   4.  View saved notes                               ║
║   5.  Run a sample question                          ║
║   0.  Exit                                           ║
╚══════════════════════════════════════════════════════╝
"""


def main():
    print(MENU)
    while True:
        choice = input("  Choose (0-5): ").strip()

        if   choice == "1": ask_question()
        elif choice == "2": view_history()
        elif choice == "3": save_note()
        elif choice == "4": view_notes()
        elif choice == "5": run_sample()
        elif choice == "0":
            print("\n  Goodbye!\n")
            break
        else:
            print("  Invalid choice. Enter 0 to 5.")

        print(MENU)


if __name__ == "__main__":
    main()
