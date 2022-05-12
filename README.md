# matgui
Streamlit webapp for generation of Nextstrain JSON from the global SARS-CoV-2 phylogeny.

## Local Server
First, prepare the environment by installing streamlit and all dependencies in the environment.yml with conda.

```
conda create -f environment.yml
conda activate matgui
conda install streamlit
```

Start a local server with streamlit run.

```
streamlit run streamlit_app.py
```

That's it!