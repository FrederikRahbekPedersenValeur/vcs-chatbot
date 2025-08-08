# vcs-chatbot

Repo indeholder 4 mapper
- backend
- frontend
- flask_test - her ligger test på RaG - virker, kræver python 3.8
- datawrangling - bearbejdelse og upload af knowledgebase. Derfra skal data stadig vektoriseres
  - - Når data er uploadet skal det vektoriseres med ada002.
    - modellen(ada002) er deployed. den tilgåes fra vcschataisearch (search services) hvor der vælges "import and vectorize data"
    - Data hentes fra cosmosdb --> knowledbebase_db --> kb_container
