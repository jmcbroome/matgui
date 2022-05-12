import streamlit as st
import bte
import os
import urllib.request
import datetime as dt
import gzip
import shutil

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
    st.markdown("# MATGUI")
    st.markdown("This is a test deployment environment for the MATGUI project.")
    st.markdown("This deployment uses a limited test dataset to demonstrate the functionality of the MATGUI project.")
    st.markdown("A full version of the project using the complete dataset is forthcoming.")
    regex = st.text_input("What samples would you like to include? Pass a valid regex matching your full sample names here (e.g. USA.* matches all samples from the USA)")
    scount = st.text_input("How many samples would you like to include?")
    clade = st.text_input("Would you like to pick a specific clade to use? E.g. B.1.1.7, B.A.2")
    use_time = st.checkbox("Use time-based filtering?")
    timestart = st.text_input("What is the earliest date you would like to include (e.g. 2020-01-01)? Default is 2019-12-01.",value="2019-12-01")
    timeend = st.text_input("What is the latest date you would like to include (e.g. 2020-01-01)? Default is today.",value=dt.date.today().strftime("%Y-%m-%d"))
    fformat = st.selectbox("Choose a file format to export", ("Nextstrain JSON", "Protobuf"))
    runbutton = st.form_submit_button(label='Generate my subtree.')

@st.experimental_singleton(suppress_st_warning=True)
def load_tree(path):
    st.write("Loading tree...")
    return bte.MATree(path)

def subsample(samples, newsamples):
    return samples.intersection(set([s.decode("UTF-8") for s in newsamples]))

#local testing mode for limited ram deployment.
path = "./testmat.pb"
with gzip.open('public-latest.metadata.tsv.gz', 'rb') as f_in:
    with open('public-latest.metadata.tsv', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

if runbutton:
    t = load_tree(path)
    print(regex, clade, timestart, timeend, fformat)
    added = 0
    leaves = t.get_leaves_ids()
    samples = set(leaves)
    print("Moving to filters.")
    if regex != "":
        st.write("Filtering {} samples by regex: {}".format(len(samples),regex))
        rsamples = t.get_regex_samples(regex)
        samples = subsample(samples, rsamples)
        st.write("Found",len(samples),"samples.")
    print("Done with regex.", len(samples))
    if clade != "":
        st.write("Filtering {} samples by regex: {}".format(len(samples),regex))
        rsamples = t.get_clade_samples(clade)
        samples = subsample(samples, rsamples)
        st.write("Found",len(samples),"samples.")
    print("Done with clade.", len(samples))
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
    print("Done with dates.", len(samples))
    if type(samples) == set:
        samples = list(samples)
    if len(samples) == 0:
        st.write("No samples found matching your selection parameters. Please try again.")
        st.stop()
    if scount != "":
        print("Doing random sampling.")
        subt = t.get_random(int(scount), [s.encode("UTF-8") for s in samples])
    else:
        subt = t.subtree(samples)
    print("Done with filtering. Looking to make output")
    if fformat == "Nextstrain JSON":
        st.write("Writing Nextstrain JSON file...")
        print("Writing json.")
        subt.write_json("subt.json", title='MATGUI Tree', metafiles=['public-latest.metadata.tsv'])
        st.write("Done!")
        st.write("Run complete. Download the result?")
        with open('subt.json', 'r') as f:
            st.download_button(label="Download Results", file_name="matgui.json", data=f.read())
    elif fformat == "Protobuf":
        st.write("Writing Protobuf file...")
        subt.save_pb("subt.pb")
        st.write("Done!")
        st.write("Run complete. Download the result?")
        with open('subt.pb', 'rb') as f:
            st.download_button(label="Download Results", file_name="matgui.pb", data=f.read())
