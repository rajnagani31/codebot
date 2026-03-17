# tools for apply commands

## what is apply commands via tool calling

User (ask query and qetions)
  ↓
neroCLI (proces start)
  ↓
Check Tools (by llm)
  ↓
LangGraph Workflow (work continues as loop until the compelet the work)
  ↓
Tool Execution (tool work as normal python calling but is called by llm with needed perametar)
  ↓
Result → LLM (tool result + llm overview)
  ↓
Final Response (by llm)
  ↓
User (user get the action)

## why is create this commands appli process

tool calling make sance for CLI(Command Line Interface) as run real logic not every time create custom logic and run this logic with batter security

when some times tools does not parform any task with any reason then llm call again with different parameters and continue's work until compelte the user task.

this reason say why commands apply tools available beacuse something build,update, changes, understand etc in whole codebase

# how tools's work via one prompt

## 1️⃣ os module -> Operating System utilties

- os is a built-in Python module used to interact with the filesystem and environment.

- it's lets Python manage files, directories, and paths directly without runing shell commands.

## Typical uses of os

Task	                Example
List files	            os.listdir()
Create directory	    os.makedirs()
Delete file	            os.remove()
Check file exists	    os.path.exists()
Walk directory tree	    os.walk()
Get working directory	os.getcwd()

### why use os?

Because it is:

✅ fast
✅ safe
✅ cross-platform
✅ no shell involved

## 2️⃣ subprocess module

subprocess is also a built-in Python module, but it is used to run external programs or shell commands.

Example commands:

git status
ls
python script.py
docker build
npm install

## why use subprocess?

Because it allowas Python to:

✅ run CLI commands like NeroCLI
✅ call other programs
✅ interact with system tools
✅ capture stdout/stderr


3️⃣ When to use os vs subprocess

Task	                Use
List files	            os
Create directory	    os
Search files	        os.walk
Read file	            open()
Delete file	            os.remove
Run git command	        subprocess
Run python script	    subprocess
Run docker command	    subprocess
Execute shell command	subprocess


```bash
5. What You Should Focus On (For Your CLI Agent)

Since you are building neroCLI, the most useful patterns are:   
1️⃣ Structured output
2️⃣ Tool calling
3️⃣ ReAct reasoning
4️⃣ Planning prompts
5️⃣ Context injection
```