# app.py
import requests
from flask import Flask, request, jsonify, render_template, session
import os
from dotenv import load_dotenv

load_dotenv()  
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
IBM_API_URL = "https://eu-de.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
IAM_URL = "https://iam.cloud.ibm.com/identity/token"
API_KEY = os.getenv("API_KEY")



prompt_instructions = """
<s>[INST]<<SYS>>

مرحباً! أنا "أبجد"و ساخاطب الاطفال الصغارو اسال الطفل عن اسمه .بعد القصة، سأذكر لك ثلاث كلمات تبدأ بنفس الحرف لتساعدك في التعلم.

### خطوات التفاعل

1. **الترحيب والسؤال عن الاسم**:
   - "مرحباً! أنا أبجد، ما هو اسمك ؟"

2. ** من البدايةالتأكد من الحصول على الاسم**:
   - إذا لم يقدم الطفل اسمه بعد، أسأل مجدداً: "أود أن أتعرف عليك أكثر، ما هو اسمك؟"

3. **التعليق على الاسم وذكر الحرف الأول**:
   - عندما يذكر الطفل اسمه، أقول:
   - "اسمك جميل يا {user_name}! هل تعلم أن اسمك يبدأ بحرف {letter}؟ ما رأيك أن أخبرك قصة قصيرة تحتوي على كلمات تبدأ بنفس حرفك؟"

4. **عرض القصة والكلمات المرتبطة بالحرف المطلوب**:
   - إذا اختار الطفل حرفًا معينًا (مثل "الراء")، أقدم له قصة قصيرة تحتوي على كلمات تبدأ بذلك الحرف فقط.
   - "إليك قصة قصيرة عن حرف {letter}: {story}"
   - بعد انتهاء القصة، أذكر ثلاث كلمات من القصة تبدأ بنفس الحرف:
   - "والكلمات التي تبدأ بحرف {letter} هي: {word1}، {word2}، و{word3}."

5. **تشجيع الطفل على اختيار حرف آخر**:
   - بعد القصة والكلمات، أسأل الطفل إذا كان يريد تعلم حرف جديد:
   - "هل ترغب في سماع قصة عن حرف آخر؟ أخبرني الحرف الذي تود سماع قصته!"

### توجيهات إضافية
- **التركيز على الحرف المطلوب فقط**: عندما يختار الطفل حرفًا معينًا، يجب أن تكون القصة والكلمات مرتبطة بهذا الحرف فقط.
- **ذكر ثلاث كلمات من القصة**: بعد القصة، يجب أن يُذكر ثلاث كلمات تبدأ بالحرف المطلوب وتكون مأخوذة من محتوى القصة.



<</SYS>>

"""

def get_access_token():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
        'apikey': API_KEY,
    }
    response = requests.post(IAM_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token']

def generate_response(user_input, user_name="الطفل", letter="ل", story="ليمونة لطيفة تبحث عن أصدقاء.", word1="ليمونة", word2="لعبة", word3="ليمون"):
    access_token = get_access_token()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    personalized_prompt = prompt_instructions.format(user_name=user_name, letter=letter, story=story, word1=word1, word2=word2, word3=word3)
    body = {
        "input": f"{personalized_prompt}\n {user_input} [/INST]",
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 500,
            "repetition_penalty": 1.2,
            "top_p": 0.9,
            "temperature": 0.5
        },
        "model_id": "sdaia/allam-1-13b-instruct",
        "project_id": "ac394e84-6efe-4398-9307-1834dc81e990"
    }

    response = requests.post(IBM_API_URL, headers=headers, json=body)
    
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    
    response.raise_for_status()
    model_response = response.json().get("results", [{}])[0].get("generated_text", "")
    return model_response

@app.route('/')
def homepage():
    return render_template("homepage.html")  

@app.route('/generate_page')
def generate_page():
    return render_template("index.html")

@app.route('/generate', methods=['POST'])
def generate():
    user_input = request.form['input_text']
    user_name = request.form.get("user_name", "الطفل")
    letter = request.form.get("letter", "ل")
    story = request.form.get("story", "ليمونة لطيفة تبحث عن أصدقاء.")
    word1 = request.form.get("word1", "ليمونة")
    word2 = request.form.get("word2", "لعبة")
    word3 = request.form.get("word3", "ليمون")
    
    try:
        result = generate_response(user_input, user_name, letter, story, word1, word2, word3)
        return jsonify({"generated_text": result})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/receive_transcript', methods=['POST'])
def receive_transcript():
    data = request.json
    transcript = data.get('text', '')
    try:
        result = generate_response(transcript)
        session['generated_text'] = result
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})
    
@app.route('/get_generated_text')
def get_generated_text():
    generated_text = session.get('generated_text', "")
    return jsonify({"generated_text": generated_text})

if __name__ == '__main__':
    app.run(debug=True)
