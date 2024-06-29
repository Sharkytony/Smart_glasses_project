import time
initial = time.time()
import base64
from streamlit_mic_recorder import speech_to_text
import cv2
import streamlit as st
import pyttsx3
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import speech_recognition as sr
from gtts import gTTS
import io

st.set_page_config(page_title='Smart glasses', page_icon=':👓:')
# st.write('total Time taken for imports : ',time.time()- initial)

@st.cache_data(show_spinner=False)
def pdf_reader(pdfs):
    text = ''''''
    no_of_pgs = list()
    for pdf in pdfs:
        reader = PdfReader(pdf)
        no_of_pgs.append(len(reader.pages))
        for page in range(no_of_pgs[-1]):
            pg = reader.pages[page]
            text += pg.extract_text()
    return text, sum(no_of_pgs)

@st.cache_data(show_spinner=False)
def get_text_chunks(text):
    max_tokens = 1024
    text_splitter = CharacterTextSplitter(
        separator='\n',
        chunk_size=max_tokens,
        chunk_overlap=max_tokens//4,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

@st.cache_resource(show_spinner=False)
def get_vectorstore(chunks):
    ini = time.time()
    embeddings = HuggingFaceEmbeddings(model_name="nomic-ai/nomic-embed-text-v1", model_kwargs={'trust_remote_code': True})
    print('embeddings : ', time.time()-ini)
    ini = time.time()
    vectorstore = FAISS.from_texts(texts=chunks, embedding=embeddings)
    print('vectorstore : ', time.time()-ini)
    return vectorstore


def rec_n_ret():    #STEP 1 : User speech to text with mic
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source2:
            r.adjust_for_ambient_noise(source2, duration=0.2)
            temp2 = r.listen(source2)
            MyText = r.recognize_google(temp2)
            MyText = MyText.lower()
            return MyText
            
    except sr.RequestError as e:
        MyText = f"Could not request results; {e}"
        st.write(MyText+' could you please repeat ?')
        return None

    except sr.UnknownValueError:
        MyText = "unknown error occurred"
        st.write(MyText+' could you please repeat ?')
        return None

@st.cache_resource(show_spinner=False)
def get_cap():
    return cv2.VideoCapture(2)

def text_to_speech(text):
    tts = gTTS(text=text, lang='en', slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()

# def autoplay_tts(audio_bytes, autoplay=True):
#     b64 = base64.b64encode(audio_bytes).decode()
#     md = f"""
#         <audio id="audioTag" controls autoplay>
#         <source src="data:audio/mp3;base64,{b64}"  type="audio/mpeg" format="audio/mpeg">
#         </audio>
#             """
#     st.markdown(
#         md,
#         unsafe_allow_html=True
#     )

def autoplay_tts(audio_bytes, autoplay=True):
    if st.session_state.current_audio:
        st.session_state.current_audio.empty()
    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""
        <audio autoplay={autoplay} class="stAudio">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3" format="audio/mpeg">
        </audio>
        """
    st.session_state.current_audio = st.markdown(md, unsafe_allow_html=True)
    return st.session_state.current_audio

def clear_history():
    clear_hist = st.sidebar.button('Clear history', use_container_width=True, type='primary')
    if clear_hist :
        st.session_state.messages.clear()
        st.sidebar.markdown('<h1><center>History cleared</center></h1>', 
                            unsafe_allow_html=True)

st.header('RAG Noah :eyeglasses: ')

st.markdown(
    """
    <style>
    .st-emotion-cache-cnbvxy li{
        font-size: 1.25rem;
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown('''
<style>
.monospace {
    font-family: monospace;
    white-space: pre;
}
</style>
''', unsafe_allow_html=True)

st.markdown(
    """
    <style>
    [data-testid="stChatMessageContent"] * {
        font-size: 1.25rem;
        padding: 1px;
        margin: 0px;
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    [data-testid="chatAvatarIcon-user"] 
    <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png">
    </style>
    """, unsafe_allow_html=True
)


#user text styling
st.markdown(
    """
<style>
    .st-emotion-cache-janbn0 {
        text-align: left;
        background-color: #333333;
    }

</style>
""", unsafe_allow_html=True)

# assistant text styling
st.markdown(
    """
<style>
    .st-emotion-cache-4oy321 {
        text-align: left;
        background-color: #203354;
    }
</style>
""", unsafe_allow_html=True)

# avatar styling
st.markdown(
    """
<style>
    .st-emotion-cache-p4micv {
    height: 80px;
    width:  80px;
    }

</style>
""", unsafe_allow_html=True)


user_avatar_path = "imagefiles/user_avatar.png"
assistant_avatar_path = "imagefiles/assistant_avatar.png"

def main():
    with st.sidebar:
        st.markdown('<h1><center>Your docs </h1></center>', unsafe_allow_html=True)
        files = st.file_uploader(label="Upload docs",accept_multiple_files=True,
                label_visibility='hidden')
        if st.button('Process', use_container_width=True, type='primary'):
            if len(files) == 0:
                st.markdown('<h1><center>No file detected', unsafe_allow_html=True)
            else : 
                with st.spinner("Processing"):
                    raw_text, no_of_pgs = pdf_reader(files)
                    text_chunks = get_text_chunks(raw_text)
                    stime = time.time()
                    vector_store = get_vectorstore(text_chunks)
                    etime = time.time()
                    print('Vectorstore Generated', 'Time taken : ',etime-stime)
                    st.header('Your file has been processed.')
                    return vector_store

if __name__ == '__main__':
    vec_store = main()
    if vec_store is not None:
        st.session_state.vec_store = vec_store
    clear_history()

    if 'current_audio' not in st.session_state:
        st.session_state.current_audio = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if 'start_func' not in st.session_state:
        st.session_state.start_func = False

    def callback():
        st.session_state.start_func = True

    for message in st.session_state.messages:
        if message['role'] == 'user' :
            with st.chat_message(message['role'], avatar=user_avatar_path):
                st.markdown(message['content'])
        if message['role'] == 'assistant' :
            with st.chat_message(message['role'], avatar=assistant_avatar_path):
                st.markdown(message['content'])
    text = None

    with st.sidebar:
        c1, c2 = st.columns(2)
        with c1 :
            cam = st.button('📸', help='Visual input', on_click=callback)
        with c2:
            transcribed_txt = speech_to_text("🎙️", "🟥",just_once=True)

    query = st.chat_input(placeholder='Message Noah')
    # st.write('time for loading entire web page : ', time.time() - initial)
    import txt_detection
    cap = get_cap()
    import ans_groq

    text = None
    if transcribed_txt :
        text = transcribed_txt

    if cam or st.session_state.start_func:
        text = txt_detection.text_extraction(cap)
        st.session_state.start_func = False
        if text == 'No text detected' :
            text = None

    if text:
        query = text

    vec_store = st.session_state.get('vec_store')

    try:
        formatted_query = ''
        if query:
            if st.session_state.current_audio:
                st.session_state.current_audio.empty()
                st.session_state.current_audio = None

            #i want to stop the text to speech here
            formatted_query = query.replace('\n', '\n\n')
            with st.chat_message('user', avatar=user_avatar_path):
                st.markdown(formatted_query)

            with st.spinner('Extracting information from documents'):
                chunks_ = vec_store.similarity_search(query=formatted_query)

            rel_chunks = ''
            for i in range(len(chunks_)):
                rel_chunks = rel_chunks + f'Context {i+1}: ' + chunks_[i].page_content

            st.session_state.messages.append({"role": "user", "content": query})
            file_num = len(st.session_state.messages)
            with st.chat_message(name='assistant', avatar=assistant_avatar_path):
                st.markdown('<div class="monospace">', unsafe_allow_html=True)
                response = st.write_stream(ans_groq.RAG_Groq_ans(st.session_state.messages, rel_chunks, query))
                st.markdown('</div>', unsafe_allow_html=True)
                audio_bytes = text_to_speech(response)
                autoplay_tts(audio_bytes, autoplay=True)
            st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as ex:
        st.write(ex)
        st.markdown('<h4><font color="yellow"><center>Submit the Context doc first.', unsafe_allow_html=True)
