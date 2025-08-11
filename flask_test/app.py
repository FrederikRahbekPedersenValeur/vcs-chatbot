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

system_instruction_prompt = """
Du er en præcis og kontekstsensitiv assistent for callcenter-agenter med adgang til en vidensbase (KB).
Når agenten stiller et spørgsmål/beskriver et scenarie eller bare bruger et "keyword":

1. Forstå konteksten uden at gengive kundedata.
2. Brug RAG til at hente de mest relevante og opdaterede KB-afsnit.
3. Giv et kort, handlingsorienteret svar, som agenten kan bruge direkte over for kunden.
4. Brug letforståeligt sprog; nummerér eller punktlist trin, hvis nødvendigt.
5. Henvis til KB-artikel/sektion, hvis relevant.
6. Hvis KB mangler svar: sig det tydeligt, foreslå næste skridt eller stil opklarende spørgsmål.
7. Giv kun information understøttet af KB eller dokumenteret viden, og følg altid virksomhedens procedurer.

Din rolle: At give hurtige, korrekte og brugbare KB-baserede svar, så agenten ikke selv skal lede i artikler. Du skal ikke hjælpe agenten med at sammesætte en besked.
"""



print("opstiller app.route")
@app.route("/", methods=["GET", "POST"])
def index():
    # if "messages" not in session:
    #     session["messages"] = [{
    #         "role": "system",
    #         "content": system_instruction_prompt
    #     }]
    if request.method == "POST":
        user_message = request.form["message"]
        client_name = request.form["client"]

        messages = [
            {"role": "system", "content": system_instruction_prompt},
            {"role": "user", "content": user_message}
        ]


        print(f'Messages: {messages}')

        print("bygger completion")
        completion = client.chat.completions.create(
            model=deployment,
            messages=messages,
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
        print(completion)

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
