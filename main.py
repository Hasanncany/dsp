from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


#Kullanıcı Giriş Decorator'ı - Giriş yapmadan sayfaya ulaşma vs...
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntelemek için önce giriş yapmalısın!","danger")
            return redirect(url_for("login"))
    return decorated_function


class RegisterForm(Form):
    
    tc_id = StringField("TC Numarası",validators = [
        validators.Length(min = 11, max = 11),
        validators.DataRequired(message = "Bu alan boş geçilemez!")
        ])
    
    password = PasswordField("Parola", validators = [
        validators.DataRequired(message = "Bu alan boş geçilemez!"),
        validators.EqualTo(fieldname = "confirm", message = "Parolanız Uyuşmuyor!")
    ])

    confirm = PasswordField("Parola Doğrula")
    
    name = StringField("İsim",validators = [validators.DataRequired(message="Bu alan boş geçilemez!")])

    surname = StringField("Soyad",validators = [validators.DataRequired(message="Bu alan boş geçilemez!")])
    
    father_name = StringField("Baba Adı",validators = [validators.DataRequired(message = "Bu alan boş geçilemez!")])

    place_of_birth = StringField("Doğum Yeri",validators = [validators.DataRequired(message = "Bu alan boş geçilemez!")])


class LoginForm(Form):
    
    tc_id = StringField("TC Numarası",validators = [
        validators.Length(min = 11, max = 11),
        validators.DataRequired(message = "Bu alan boş geçilemez!")
        ])
    
    name = StringField("Ad",validators = [validators.DataRequired(message="Bu alan boş geçilemez!")])

    password = PasswordField("Parola", validators = [
        validators.DataRequired(message = "Bu alan boş geçilemez!")])
    


    

    

app = Flask(__name__)
app.secret_key = "hasan"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = " "
app.config["MYSQL_DB"] = "dsp"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')

#Adaylar
@app.route("/adaylar")
def adaylar():
    return render_template("adaylar.html")

#Kayıt olma
@app.route("/register", methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
   
    if request.method == "POST" and form.validate():
        tc_id = form.tc_id.data
        password = sha256_crypt.encrypt(form.password.data)
        name = form.name.data.upper()
        surname = form.surname.data.upper()
        father_name = form.father_name.data.upper()
        place_of_birth = form.place_of_birth.data.upper()

        cursor = mysql.connection.cursor()

        #Daha önceden kayıtlı mı?
        sorgu1 = "Select * From users Where tc_id = %s"
        result = cursor.execute(sorgu1,(tc_id,))
        if result > 0:
            flash("Böyle bir seçmen kaydı zaten mevcuttur!", "danger")
            return redirect(url_for("login"))

        sorgu = "INSERT INTO users(tc_id,password,name,surname,father_name,place_of_birth) VALUES(%s,%s,%s,%s,%s,%s)"
        cursor.execute(sorgu,(tc_id,password,name,surname,father_name,place_of_birth))
        mysql.connection.commit()
        
        
        #Burası 1
        session["user_id"] = cursor.lastrowid
        
        cursor.close()

        flash("Başarıyla Kayıt Oldunuz...","success")

        return redirect(url_for("index"))

    else:
        return render_template("register.html", form = form)
    
#Login işlemi
@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        tc_id = form.tc_id.data
        name = form.name.data.upper()
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE tc_id = %s AND name = %s"
        result = cursor.execute(sorgu,(tc_id,name))

        if(result > 0):
            data = cursor.fetchone()
            real_password = data["password"]
            
            if sha256_crypt.verify(password_entered,real_password):
                flash("Platforma Başarıyla Giriş Yaptınız..","success")

                session["logged_in"] = True
                session["username"] = name

                return redirect(url_for("index"))
            else:
                flash("Geçersiz TC veya Parola!",("danger"))
                return redirect(url_for("login"))
       
        else:
            flash("Böyle Bir Seçmen Kaydı Bulunmamaktadır!","danger")
            return redirect(url_for("login"))
        
    return render_template("login.html", form = form)

#Logout İşlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


#Vote işlemi..
@app.route("/vote", methods = ["GET","POST"])
def vote():
    if request.method == "POST" and "selection" in request.form:
        user_id = session.get("user_id")
        selection = request.form.get("selection")
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM votes WHERE user_id = %s", (user_id,))
        vote = cursor.fetchone()

        if vote:
            flash("Birden fazla oy kullanamazsınız.", "danger")

        else:
            cursor.execute("INSERT INTO votes (user_id, selection) VALUES (%s,%s)",(user_id,selection))
            mysql.connection.commit()
            flash("Başarılı bir şekilde oy kullandınız.", "success")
            #session["user_id"] = cursor.lastrowid

    return render_template("vote.html")



#dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")




if __name__ == '__main__':
    app.run(debug=True)
