# ─────────────────────────────────────────────────────────────
#     EMAIL AI AGENT — LANGCHAIN + GOOGLE GEN AI + YAGMAIL
#     Features: AI Content | Login | Security | MongoDB
# ─────────────────────────────────────────────────────────────

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pymongo import MongoClient
import yagmail
import streamlit as st
import datetime
import time

# ─────────────────────────────────────────
# CSS — Professional UI
# ─────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: white;
        border-radius: 15px;
        padding: 20px;
    }
    .stButton button {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    h1 {
        color: white !important;
        text-align: center;
        font-size: 3rem !important;
    }
    h2, h3 {
        color: #667eea !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# LOGIN SYSTEM
# ─────────────────────────────────────────
users = {
    "hassan" : {"password": "pharm123",  "name": "Hassan"},
    "client1": {"password": "client123", "name": "Client One"},
    "client2": {"password": "client456", "name": "Client Two"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("📧 Email AI Agent")
    st.markdown("<h3 style='text-align:center; color:white;'>Please login to continue</h3>",
                unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("👤 Username:")
        password = st.text_input("🔐 Password:", type="password")
        if st.button("Login", use_container_width=True):
            if username in users and users[username]["password"] == password:
                st.session_state.logged_in   = True
                st.session_state.username    = username
                st.session_state.user_name   = users[username]["name"]
                st.rerun()
            else:
                st.error("❌ Wrong username or password")
    st.stop()

# ─────────────────────────────────────────
# STEP 1 — Setup LLM
# ─────────────────────────────────────────
API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyDRiuy9l6d6qapsXlhcllIuPoxAsWbWK78")

llm = ChatGoogleGenerativeAI(
    api_key=API_KEY,
    model="gemini-2.5-flash",
    temperature=0.7
)

# ─────────────────────────────────────────
# STEP 2 — Gmail Setup
# ─────────────────────────────────────────
GMAIL_USER     = "khnbutt118@gmail.com"
GMAIL_PASSWORD = st.secrets.get("GMAIL_PASSWORD", "qiws tgem rthb qtjc")

# ─────────────────────────────────────────
# STEP 3 — MongoDB Setup
# ─────────────────────────────────────────
MONGODB_URI = st.secrets.get("MONGODB_URI", "mongodb+srv://khnbutt118_db_user:QLaFKV8usDNC9VEd@cluster0.7s3p0bb.mongodb.net/")
client      = MongoClient(MONGODB_URI)
db          = client["email_agent"]

subscribers_col = db["subscribers"]
sent_topics_col = db["sent_topics"]
logs_col        = db["email_logs"]

# ─────────────────────────────────────────
# STEP 4 — AI Email Generator
# ─────────────────────────────────────────
def generate_email_content(topic: str, recipient_name: str) -> dict:
    prompt = PromptTemplate.from_template("""
    You are Hassan, a PharmD student and AI in Pharmacy enthusiast.
    Write a professional and engaging medical newsletter email.
    
    Recipient Name : {name}
    Topic          : {topic}
    Today's Date   : {date}
    
    Write the email with:
    - Personalized greeting using recipient name
    - Engaging subject line
    - Educational medical content about the topic
    - 3-5 key points in simple language
    - A call to action (visit LinkedIn, YouTube, or website)
    - Professional sign-off from Hassan
    - Disclaimer: For educational purposes only
    
    Format your response as:
    SUBJECT: [subject line here]
    BODY: [full email body here]
    """)
    chain  = prompt | llm | StrOutputParser()
    result = chain.invoke({
        "name" : recipient_name,
        "topic": topic,
        "date" : datetime.datetime.now().strftime("%B %d, %Y")
    })
    lines   = result.strip().split("\n")
    subject = ""
    body    = ""
    for i, line in enumerate(lines):
        if line.startswith("SUBJECT:"):
            subject = line.replace("SUBJECT:", "").strip()
        elif line.startswith("BODY:"):
            body = "\n".join(lines[i+1:]).strip()
    return {"subject": subject, "body": body}

# ─────────────────────────────────────────
# STEP 5 — Instagram Caption Generator
# ─────────────────────────────────────────
def generate_instagram_caption(topic: str) -> str:
    prompt = PromptTemplate.from_template("""
    You are Hassan, a PharmD student running @HealthyHorizons on Instagram.
    Write a short engaging Instagram caption about: {topic}
    
    Include:
    - Hook in first line (attention grabbing)
    - 3 key points maximum
    - Call to action (link in bio)
    - 8-10 relevant hashtags
    - Max 150 words total
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"topic": topic})

# ─────────────────────────────────────────
# STEP 6 — Email Sender
# ─────────────────────────────────────────
def send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        yag = yagmail.SMTP(GMAIL_USER, GMAIL_PASSWORD)
        yag.send(to=to_email, subject=subject, contents=body)
        logs_col.insert_one({
            "to"     : to_email,
            "subject": subject,
            "sent_at": datetime.datetime.now(),
            "status" : "sent"
        })
        return True
    except Exception as e:
        logs_col.insert_one({
            "to"     : to_email,
            "subject": subject,
            "sent_at": datetime.datetime.now(),
            "status" : f"failed: {str(e)}"
        })
        return False

# ─────────────────────────────────────────
# STEP 7 — Subscriber Management
# ─────────────────────────────────────────
def add_subscriber(name: str, email: str) -> bool:
    if subscribers_col.find_one({"email": email}):
        return False
    subscribers_col.insert_one({
        "name"         : name,
        "email"        : email,
        "subscribed_at": datetime.datetime.now(),
        "active"       : True
    })
    welcome = generate_email_content("Welcome to Hassan's Medical AI Newsletter", name)
    send_email(email, welcome["subject"], welcome["body"])
    return True

def get_all_subscribers() -> list:
    return list(subscribers_col.find({"active": True}))

def unsubscribe(email: str):
    subscribers_col.update_one({"email": email}, {"$set": {"active": False}})

# ─────────────────────────────────────────
# STEP 8 — Send Newsletter to All
# ─────────────────────────────────────────
def send_newsletter_to_all(topic: str):
    subscribers = get_all_subscribers()
    if not subscribers:
        return 0, 0
    success = 0
    failed  = 0
    for sub in subscribers:
        content = generate_email_content(topic, sub["name"])
        result  = send_email(sub["email"], content["subject"], content["body"])
        if result:
            success += 1
        else:
            failed += 1
        time.sleep(2)
    sent_topics_col.insert_one({
        "topic"  : topic,
        "sent_at": datetime.datetime.now(),
        "success": success,
        "failed" : failed
    })
    return success, failed

# ─────────────────────────────────────────
# STEP 9 — Streamlit UI
# ─────────────────────────────────────────
st.title("📧 Email AI Agent")
st.markdown(
    f"<p style='text-align:center; color:white;'>Welcome, "
    f"<b>{st.session_state.user_name}</b> | "
    f"<a href='#' style='color:#ffd700;'>Logout</a></p>",
    unsafe_allow_html=True
)

# Subscriber count display
total_subs = len(get_all_subscribers())
st.markdown(
    f"<p style='text-align:center; color:white; font-size:1.2rem;'>"
    f"📊 Total Subscribers: <b>{total_subs}</b></p>",
    unsafe_allow_html=True
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📤 Send Newsletter",
    "📱 Instagram",
    "👥 Subscribers",
    "➕ Add Subscriber",
    "📊 Logs"
])

# ── Tab 1: Send Newsletter ──
with tab1:
    st.subheader("Send AI-Generated Newsletter")
    st.write("**Suggested Topics:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💊 Drug Spotlight"):
            st.session_state.topic = "Drug Spotlight — Amlodipine for Hypertension"
        if st.button("🧬 Pharmacogenomics"):
            st.session_state.topic = "How Genes Affect Drug Response — Pharmacogenomics"
        if st.button("🤖 AI in Pharmacy"):
            st.session_state.topic = "How AI is Transforming Pharmacy Practice"
    with col2:
        if st.button("⚠️ Drug Interactions"):
            st.session_state.topic = "5 Critical Drug Interactions Every Student Must Know"
        if st.button("📋 Clinical Tips"):
            st.session_state.topic = "Patient Counseling Tips for Pharmacists"
        if st.button("🎓 PharmD Tips"):
            st.session_state.topic = "Study Tips for PharmD Students"

    topic = st.text_input("Email Topic:", value=st.session_state.get("topic", ""))

    if st.button("👁️ Preview Email"):
        if topic:
            with st.spinner("Generating preview..."):
                preview = generate_email_content(topic, "Valued Subscriber")
            st.subheader("Subject:")
            st.write(preview["subject"])
            st.subheader("Body:")
            st.write(preview["body"])

    st.divider()

    if st.button("🚀 Send to All Subscribers", type="primary"):
        if topic:
            subs = get_all_subscribers()
            if not subs:
                st.warning("No subscribers yet!")
            else:
                progress = st.progress(0)
                with st.spinner(f"Sending to {len(subs)} subscribers..."):
                    success, failed = send_newsletter_to_all(topic)
                    progress.progress(100)
                st.success(f"✅ Sent: {success} | ❌ Failed: {failed}")
        else:
            st.warning("Please enter a topic first!")

    st.divider()
    st.subheader("📬 Send Test Email")
    test_email = st.text_input("Test email address:")
    test_name  = st.text_input("Recipient name:", value="Hassan")
    if st.button("Send Test"):
        if topic and test_email:
            with st.spinner("Sending test email..."):
                content = generate_email_content(topic, test_name)
                result  = send_email(test_email, content["subject"], content["body"])
            if result:
                st.success("✅ Test email sent successfully!")
            else:
                st.error("❌ Failed to send test email")

# ── Tab 2: Instagram ──
with tab2:
    st.subheader("📱 Instagram Caption Generator")
    st.write("Generate captions for your **Healthy Horizons** account")
    insta_topic = st.text_input("Topic for Instagram post:")
    if st.button("✨ Generate Caption"):
        if insta_topic:
            with st.spinner("Generating Instagram caption..."):
                caption = generate_instagram_caption(insta_topic)
            st.subheader("📋 Your Caption:")
            st.text_area("Copy this:", value=caption, height=300)
            st.info("💡 Tip: Post this on Instagram and add 'Link in bio' to drive subscribers!")
        else:
            st.warning("Please enter a topic!")

# ── Tab 3: Subscribers ──
with tab3:
    st.subheader("👥 Current Subscribers")
    subs = get_all_subscribers()
    if subs:
        st.write(f"**Total active subscribers: {len(subs)}**")
        for sub in subs:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(sub["name"])
            with col2:
                st.write(sub["email"])
            with col3:
                if st.button("Remove", key=sub["email"]):
                    unsubscribe(sub["email"])
                    st.rerun()
    else:
        st.info("No subscribers yet!")

# ── Tab 4: Add Subscriber ──
with tab4:
    st.subheader("➕ Add New Subscriber")
    new_name  = st.text_input("Name:")
    new_email = st.text_input("Email:")
    if st.button("Add Subscriber"):
        if new_name and new_email:
            result = add_subscriber(new_name, new_email)
            if result:
                st.success(f"✅ {new_name} added! Welcome email sent.")
            else:
                st.warning("This email is already subscribed!")
        else:
            st.warning("Please fill both name and email!")

# ── Tab 5: Logs ──
with tab5:
    st.subheader("📊 Email Logs")
    logs = list(logs_col.find().sort("sent_at", -1).limit(20))
    if logs:
        for log in logs:
            status_icon = "✅" if log["status"] == "sent" else "❌"
            st.write(
                f"{status_icon} **{log['to']}** — "
                f"{log['subject'][:50]}... — "
                f"{log['sent_at'].strftime('%Y-%m-%d %H:%M')}"
            )
    else:
        st.info("No emails sent yet.")