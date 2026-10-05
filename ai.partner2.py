import streamlit as st

import os
from openai import OpenAI
from datetime import datetime
import json


st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="🧘‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


#保存会话信息
def save_session():
    if st.session_state.messages:
        # 构建新的会话对象
        session_data = {
            "current_session": st.session_state.current_session,

            "nick": st.session_state.nick,
            "character": st.session_state.character,
            "messages": st.session_state.messages
        }

        # 创建文件夹
        if not os.path.exists("session"):
            os.makedirs("session")

        # 保存会话数据
        with open(f"session/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

#加载所有的会话列表信息
def load_session():
    session_list=[]
    #加载sessions目录下的文件
    if os.path.exists("session"):
        file_list=os.listdir("session")
        for file_name in file_list:
            if file_name.endswith(".json"):
                session_list.append(file_name[:-5:1])
    session_list.sort(reverse=True)#排序，默认是False，这里改为True。降序
    return session_list
#加载指定会话信息
def load_sessions(session_name):
    try:
        if os.path.exists(f"session/{session_name}.json"):
            # 读取会话数据
            with open(f"session/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick = session_data["nick"]
                st.session_state.character = session_data["character"]
                st.session_state.current_session = session_name
    except Exception as e:
        st.error("会话加载失败")

#删除会话
def delete_session(session_name):
    try:
        if os.path.exists(f"session/{session_name}.json"):
            os.remove(f"session/{session_name}.json")#删除文件
            #删除当前列表后需要更新消息列表
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception :
        st.error("会话删除失败")


st.title("AI智能伴侣")

#st.logo("resource/111.jpeg")


#系统提示词
system_prompt = """
        你叫%s，现在是用户的真实伴侣，请完全代入伴侣角色。
        规则：
            1：每次只回一条消息
            2：禁止任何场景或状态描述性文字
            3：匹配用户语言
            4：回复简短，像微信聊天一样
            5：有需要的话可以用emoji表情
            6：用符号伴侣性格的方式对话
            7：回复的内容，要充分体现伴侣的性格特征
        伴侣特征：
            %s
        你必须严格遵守上述规则来回复用户

"""



#初始化聊天信息
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'nick' not in st.session_state:
    st.session_state.nick = "清清"
if 'character' not in st.session_state:
    st.session_state.character = "友好,关心,幽默,内耗,有一点耐心,有同理心,有责任感,你是男生,你说话还是有分寸的，并且喜欢开玩笑"
#会话名称
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()


#展示聊天信息
st.text(f"会话名称:{st.session_state.current_session}")
for message in st.session_state.messages:
     if message["role"] == "user":
         st.chat_message("user").write(message["content"])
     else:
         st.chat_message("assistant").write(message["content"])



client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

#左侧侧边栏-with:streamlit中上下文的管理器
with st.sidebar:
    st.subheader("AI控制面板")

    #新建会话按钮
    if st.button("新建会话",width="stretch",icon="💍"):
        #保存当前会话信息
        save_session()
        #创建新会话
        if st.session_state.messages:
           st.session_state.messages = []
           st.session_state.current_session = generate_session_name()
           save_session()
           st.rerun()  # 重新运行当前页面

    #历史会话
    st.text("历史会话")
    session_list=load_session()
    with st.container(height=150):
        for session in session_list:
            col1, col2 = st.columns([4, 1])
            with col1:

                # 三元运算符：为真返回第一个，微假返回第二个
                if st.button(session, width="stretch", icon="🏮", key=f"session_{session}",
                             type="primary" if session == st.session_state.current_session else "secondary"):
                    load_sessions(session)
                    st.rerun()
            with col2:
                if st.button("", width="stretch", icon="❌", key=f"delete_{session}"):
                    delete_session(session)
                    st.rerun()

    #分割线
    st.divider()

    #伴侣信息
    st.subheader("伴侣信息")
    # 昵称输入框
    nick = st.text_input("昵称", placeholder="请输入伴侣的昵称", value=st.session_state.nick)#placeholder:提示信息
    if nick:
        st.session_state.nick = nick
    #性格输入框
    character=st.text_area("性格",placeholder="请输入伴侣的性格",value=st.session_state.character)#文本域
    if character:
        st.session_state.character = character





#聊天框
prompt = st.chat_input("请输入您要问的问题")
if prompt:
    st.chat_message("user").write(prompt)
    print("-----> 调用AI大模型，提示词:",prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})


    #调用AI大模型
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick, st.session_state.character)},
            *st.session_state.messages,#解包
        ],


        stream=True,#True是流式输出，False是非流式输出
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )
    #输出大模型响应结果（非流式输出）
    # print("<------大模型返回的结果",response.choices[0].message.content)
    # st.chat_message("assistant").write(response.choices[0].message.content)

    #流式输出
    response_message=st.empty()



    full_response=""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content=chunk.choices[0].delta.content
            full_response+=content
            response_message.chat_message("assistant").write(full_response)
    #保存大模型返回结果
    st.session_state.messages.append({"role": "assistant", "content": full_response})


    #保存会话信息
    save_session()
