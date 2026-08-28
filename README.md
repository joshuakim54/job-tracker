Hi my name is Josh. I built a job tracker specifically for software engineering but am tweaking it so my girlfriend and other friends can use it for various fields. I also recommend using https://chromewebstore.google.com/detail/simplify-copilot-autofill/pbanhockgagggenencehbnadejlgchfc just to make applying to jobs a bit easier. I built this because I felt like LinkedIn had a lot of ghost listings and old job listings. This pulls directly from a companies career website. 

## Streamlit GUI

The browser-based search interface is in `app.py`. It lets you search selected company career sites with custom role, location, include, and exclude terms.

Run it locally with:

```bash
pip install -r requirements.txt
streamlit run app.py
```

To publish it, push the repository to GitHub and deploy it from [Streamlit Community Cloud](https://share.streamlit.io/). Select `app.py` as the main file and `requirements.txt` will be installed automatically. GitHub Pages cannot run this Python app.

For internships, enter `internship` in **Role keywords** and remove `intern` or `internship` from **Exclude** if either is present.
