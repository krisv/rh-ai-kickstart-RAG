If the user asks to create their own agent, help them by following this plan.
This project contains a folder idea-vault-agent that is an example of how to implement an agent using langchain and langgraph.  Let's create a copy of this for the user and then update this according to their requirements.  To do so, follow the following steps precisely.  Show the different steps to the user clearly.

1. Ask a name for their agent.  Create a folder with that name (make suggest an alternative if the user uses illegal characters) and copy the content of the idea-vault-agent folder in that new folder.

2. Ask the user what they want the agent to do.  Update the app.py file, removing the agents there and adding a LangGraph agent similar to what was there but implementing what the user requested.  Only make changes if necessary, try to keep the code as similar as possible to the original where possible.

3. Update the app.py submit_idea() operation with an operation matching the new use case that will trigger the agent.

4. Update the index.html to have a simple web UI that can be used to trigger the agent through this method.  Use default-agent.png for the image.

5. Read the readme.txt and update the title with the new agent name.

6. Update the test_app.py if necessary.

7. Run a command to create the virtual environment, and install dependencies from requirements file.  Don't start the service, but ask the user if he wants to execute the agent himself locally or he wants you to start it in the background.  Note that starting it himself will show the console output better.  

    7a. If the user wants you to start the service, execute the command to start the new agent.  
    
    7b. Otherwise, show the commands he can just copy to execute in a separate terminal.  Start with a command to go into the agent folder first to keep the commands simple.  Next source the virtual environment and start the server.  Do not suggest to execute the command yourself. Then wait for the user to confirm it seems to have started correctly.

8. Execute pytest to see if the agent is working.

9. If everything seems to be working, ask the user to try himself and provide him the right URL.