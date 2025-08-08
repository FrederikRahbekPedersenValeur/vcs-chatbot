import os
from flask import Flask, render_template, request, session, redirect
from openai import AzureOpenAI #kræver python 3.8 eller nyere
from dotenv import load_dotenv


KUNDER = [
    "Airtox",
    "Barons",
    "Billund Lufthavn",
    "Dansk Psykolog Forening",
    "Forbrugsforeningen",
    "Gastromé",
    "Gastrotools2",
    "Heartland",
    "Hjem-IS",
    "Imbox",
    "KIBO Sikring",
    "Kingsland",
    "Kop _ Kande",
    "Livenation",
    "Magasin",
    "PanzerGlass",
    "Pilgrim",
    "Seges",
    "Sport24",
    "Søstrene Grene",
    "Tankesport",
    "Wellvita"
]

load_dotenv()
app = Flask(__name__)
app.secret_key = "hemmelig-nøgle"  # Brug evt. os.urandom i produktion

# Azure OpenAI opsætning
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2025-01-01-preview",
)

deployment = os.getenv("AZURE_OAI_DEPLOYMENT", "gpt-4.1-mini")
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_KEY")
search_index = os.getenv("AZURE_SEARCH_INDEX", "rag-nyt-index")

print("opstiller app.route")
@app.route("/", methods=["GET", "POST"])
def index():
    if "messages" not in session:
        session["messages"] = [{
            "role": "system",
            "content": "You are an AI assistant that helps people find information."
        }]
    if request.method == "POST":
        user_message = request.form["message"]
        client_name = request.form["client"]

        session["messages"].append({"role": "user", "content": user_message})

        print("bygger completion")
        completion = client.chat.completions.create(
            model=deployment,
            messages=session["messages"],
            max_tokens=800,
            temperature=1,
            stream=False,
            extra_body={
                "data_sources": [{
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": search_endpoint,
                        "index_name": search_index,
                        "semantic_configuration": "default",
                        "query_type": "vector",
                        "fields_mapping": {
                            "content_fields_separator": "\n",
                            "content_fields": ["text"],
                            "filepath_field": "source_file",
                            "title_field": None,
                            "url_field": None,
                            "vector_fields": ["vector"]
                        },
                        "in_scope": True,
                        "filter": f"client eq '{client_name}'",
                        "strictness": 3,
                        "top_n_documents": 5,
                        "authentication": {
                            "type": "api_key",
                            "key": search_key
                        },
                        "embedding_dependency": {
                            "type": "deployment_name",
                            "deployment_name": "text-embedding-ada-002"
                        }
                    }
                }]
            }
        )

        ai_reply = completion.choices[0].message.content
        session["messages"].append({"role": "assistant", "content": ai_reply})

    print("render template")

    return render_template("chat.html", messages=session["messages"], kunder=KUNDER)



@app.route("/reset")
def reset():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
