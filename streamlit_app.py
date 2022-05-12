from numpy import std
import streamlit as st
import bte
import os
import urllib.request
import datetime as dt
import gzip
import shutil
import random
import sys

from streamlit.scriptrunner import get_script_run_ctx
def _get_session():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise Exception("Failed to get the thread context")            
    return ctx.session_id

def retrieve_file(fn):
    if not os.path.exists(fn):
        print("Retrieving data from the UCSC public repository...")
        urllib.request.urlretrieve("http://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/public-latest.all.masked.pb", "public-latest.all.masked.pb")
        urllib.request.urlretrieve("http://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/public-latest.metadata.tsv.gz", "public-latest.metadata.tsv.gz")
        with gzip.open('public-latest.metadata.tsv.gz', 'rb') as f_in:
            with open('public-latest.metadata.tsv', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        st.write("Data successfully downloaded!")

with st.form(key="matgui"):
    st.title("MATGUI")
    st.markdown("This webtool allows the user to generate a customized Nextstrain view of the SARS-CoV-2 pandemic by generating an Auspice-compatible JSON.")
    st.markdown("The JSON files produced by this tool can be uploaded to [Auspice](https://auspice.us/) for viewing. Just download then drag and drop!")
    samplelist = st.text_area("Paste a list of samples to include, one per line.")
    regex = st.text_input("What category of sample names would you like to include? Pass a valid regex matching your full sample names of interest here (e.g. USA.* matches all samples from the USA)")
    clade = st.text_input("Would you like to select a specific clade? E.g. B.1.1.7, B.A.2")
    use_time = st.checkbox("Use time-based filtering?")
    timestart = st.text_input("What is the earliest date you would like to include (e.g. 2020-01-01)? Default is 2019-12-01.",value="2019-12-01")
    timeend = st.text_input("What is the latest date you would like to include (e.g. 2020-01-01)? Default is today.",value=dt.date.today().strftime("%Y-%m-%d"))
    scount = st.text_input("How many total samples matching your criteria would you like to include in your final output? Default is all.")
    background = st.text_input("How many background samples (samples not matching these criteria) would you like to include in your final output? Default is none.")
    fformat = st.selectbox("Choose a file format to export", ("Nextstrain JSON", "Protobuf"))
    runbutton = st.form_submit_button(label='Generate my subtree.')

@st.experimental_singleton(suppress_st_warning=True)
def load_tree(path):
    st.write("Loading tree...")
    return bte.MATree(path)

def subsample(samples, newsamples):
    return samples.intersection(set([s.decode("UTF-8") if type(s) == bytes else s for s in newsamples]))

path = "public-latest.all.masked.pb"
pref = _get_session()
if runbutton:
    retrieve_file(path)
    t = load_tree(path)
    added = 0
    leaves = t.get_leaves_ids()
    samples = set(leaves)
    if samplelist != "":    
        samples = subsample(samples, samplelist.splitlines())
    if regex != "":
        st.write("Filtering {} samples by regex: {}".format(len(samples),regex))
        rsamples = t.get_regex_samples(regex)
        samples = subsample(samples, rsamples)
        st.write("Found",len(samples),"samples.")
    if clade != "":
        st.write("Filtering {} samples by regex: {}".format(len(samples),regex))
        rsamples = t.get_clade_samples(clade)
        samples = subsample(samples, rsamples)
        st.write("Found",len(samples),"samples.")
    if use_time:
        st.write("Filtering {} samples by time: {} to {}".format(len(samples),timestart,timeend))
        tsamples = []
        for s in list(samples):
            try:
                date = dt.datetime.strptime(s[s.rfind("|")+1:],'%Y-%m-%d')
                if date >= dt.datetime.strptime(timestart,'%Y-%m-%d') and date <= dt.datetime.strptime(timeend,'%Y-%m-%d'):
                    tsamples.append(s)
            except:
                continue
        st.write("Found",len(tsamples),"samples.")
        samples = tsamples
    if type(samples) == set:
        samples = list(samples)
    if len(samples) == 0:
        st.write("No samples found matching your selection parameters. Please try again.")
        st.stop()
    if scount != "" or background != "":
        if scount != "":
            target = int(scount)
            if target < len(samples):
                samples = random.sample(samples, target)
        else:
            target = len(samples)
        if background != "":
            if fformat == "Nextstrain JSON":
                with open(pref+"_sel.txt","w+") as outf:
                    outf.write("sample\tSelection\n")
                    outf.write("\tselected\n".join(samples)+'\tselected\n')
            target += int(background)
        subt = t.get_random(target, [s.encode("UTF-8") for s in samples])
    else:
        subt = t.subtree(samples)
    if fformat == "Nextstrain JSON":
        st.write("Writing Nextstrain JSON file...")
        mf = ['public-latest.metadata.tsv']
        if background != "":
            mf.append(pref + "_sel.txt")
        subt.write_json(pref+"_subt.json", title='MATGUI Tree', metafiles=mf)
        st.write("Done!")
        st.write("Run complete. Download the result?")
        with open(pref+'_subt.json', 'r') as f:
            db = st.download_button(label="Download Results", file_name="matgui.json", data=f.read())
            if db:
                print("Clearing temporary files.",file=sys.stderr)
                for seshfile in [pref+"_sel.txt", pref+"_subt.json"]:
                    if os.path.exists(seshfile):
                        os.remove(seshfile)
    elif fformat == "Protobuf":
        st.write("Writing Protobuf file...")
        subt.save_pb(pref+"_subt.pb")
        st.write("Done!")
        st.write("Run complete. Download the result?")
        with open(pref+'_subt.pb', 'rb') as f:
            db = st.download_button(label="Download Results", file_name="matgui.pb", data=f.read())
            if db:
                print("Clearing temporary files.",file=sys.stderr)
                for seshfile in [pref+"_subt.pb"]:
                    if os.path.exists(seshfile):
                        os.remove(seshfile)