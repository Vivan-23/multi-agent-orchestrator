from src.Agents.agents import research_agent, Summarization_agent, Reviewer_agent

def run_pipeline(input):
    state = {"input":input, "steps" : [],
              "data": None, "summary" : None, "output": None}
    
    state = research_agent(state)
    state = Summarization_agent(state)
    state = Reviewer_agent(state)
    return state
