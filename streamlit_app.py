import streamlit as st
from openai import OpenAI
from graph import GraphModel
from sidebar import *
from langchain_core.messages import HumanMessage
import time



# Function to save selected prompt to session state
def save_prompt(prompt_key):
    st.session_state.selected_prompt = predefined_prompts[prompt_key]


def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

SYSTEM_PROMPT = "You are a helpful, respectful and honest assistant."

high_mast_prompt = [
    "Use the texts supplied above to answer the user's question. Present a prominent and clear main analytic message. Present clear reasoning with no flaws in logical and effectively combine evidence, context, and assumptions to support analytic judgments. Use clear language and a structure that displays a logical flow appropriate for the presented argument. Address inconsistent or contrary information in a way that reconciles it with your analytic judgments. Also, provide a list of the evidential documents supporting your answer.",
    "Consistently distinguish among statements that convey underlying information, assumptions, and judgments. Explicitly state assumptions that serve as linchpins of an argument or bridge key information gaps. Explain the implications for judgments if assumptions are incorrect. Identify indicators that, if detected, could validate or refute assumptions. ",
    "Provide detailed source descriptors, summarize the sources, assess their strengths and weaknesses. Discuss the linkage of sources to your analysis and judgments. Provide a detailed description of factors that could affect source quality and credibility.",
    "Provide especially thorough discussion of nature and source of uncertainties affecting major analytic judgments. Identify indicators, that if detected, would alter levels of uncertainty associated with major analytic judgments.",
    "Are there any likely alternative analyses due to uncertainties, complexity, or low probability/high impact situations? Explain the evidence and reasoning that underpin them. Discusses their likelihood or implications. Identify indicators that would, if detected, affect the likelihood of any identified alternatives.",
    "Provide assurances (e.g., % of confidence that the judgment is correct) and clearly identify the specific reason underlying this assessment. I need to independently determine that your results are accurate, complete, and consistent."
]

high_mast_prompt = "\n".join(high_mast_prompt)

# Initialize OpenAI client and GraphModel
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

graph_model = GraphModel()



# Set the title for the Streamlit app
st.title("MASTOPIA Demo - Low Performance Low MAST")


###########
# Buttons #
###########

# Define your predefined prompts
predefined_prompts = {
    "Prompt 1": "For every individual mentioned, create a profile with the most important information about them, list their relationships to other individuals, and list in which articles they appear.",
    "Prompt 2": "Group all articles into several topics. Provide the topics and which articles are contained in each topic",
    "Prompt 3": "Identify any imminent terrorist threats in the Vastopolis metropolitan area. Provide detailed information on the threat or threats (e.g. who, what, where, when, and how) so that officials can conduct counterintelligence activities. Also, provide a list of the evidential documents supporting your answer."
}

# Define CSS style for button size
button_style = """
    <style>
    .stButton button {
        width: 200px; /* Adjust width as needed */
        height: 50px; /* Adjust height as needed */
        font-size: 16px; /* Adjust font size as needed */
    }
    </style>
"""

# Display CSS style
st.markdown(button_style, unsafe_allow_html=True)

# Create a horizontal layout for buttons
button_col1, button_col2, button_col3 = st.columns(3)

# Display predefined prompts in columns
with button_col1:
    if st.button("Prompt 1"):
        save_prompt("Prompt 1")

with button_col2:
    if st.button("Prompt 2"):
        save_prompt("Prompt 2")

with button_col3:
    if st.button("Prompt 3"):
        save_prompt("Prompt 3")

###########





# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]




# Add a sidebar for document search
with st.sidebar:
    st.title("Search Documents")
    search_query = st.text_input("Enter document id")
    if search_query:
        search_results = search_documents(search_query)
        # st.write(search_results)




# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])



# Accept user input
# if prompt := st.chat_input("What is up?"):

# Determine if a predefined prompt is selected


if prompt := st.chat_input("What is up?"):
    input_message = {"messages": [HumanMessage(content=prompt + high_mast_prompt)]}


    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Execute the graph with the input message
    result_generator = graph_model.execute(input_message)

    # Extract the assistant's reply
    assistant_reply = ""
    for response in result_generator:
        print(response)
        if "__end__" not in response and assistant_reply == "":
            for key, value in response.items():
                if key in ["Searcher", "Retriever"]:
                    assistant_reply = value["messages"][0].content
                    break

    if assistant_reply == "":
        assistant_reply = "Sorry, I didn't understand that."

    # Display assistant's message in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(assistant_reply))

        # st.markdown(assistant_reply)

    
    # Add assistant's message to chat history
    st.session_state.messages.append({"role": "assistant", "content": response}) # "content": assistant_reply


if 'selected_prompt' in st.session_state:
    print(st.session_state)
    prompt = st.session_state.selected_prompt
    print("prompt: ", prompt)
    input_message = {"messages": [HumanMessage(content=prompt)]}
        

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Execute the graph with the input message
    result_generator = graph_model.execute(input_message)

    # Extract the assistant's reply
    assistant_reply = ""
    for response in result_generator:
        print(response)
        if "__end__" not in response and assistant_reply == "":
            for key, value in response.items():
                if key in ["Searcher", "Retriever"]:
                    assistant_reply = value["messages"][0].content
                    break

    if assistant_reply == "":
        assistant_reply = "Sorry, I didn't understand that."

    # Add assistant's message to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    # Display assistant's message in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(assistant_reply))

        # st.markdown(assistant_reply)

    del st.session_state['selected_prompt']


