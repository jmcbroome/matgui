# matgui
Streamlit webapp for generation of customized Nextstrain JSON from the global SARS-CoV-2 phylogeny. 
Produces Auspice JSONs that can be uploaded at [Auspice](https://auspice.us/) for viewing.

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