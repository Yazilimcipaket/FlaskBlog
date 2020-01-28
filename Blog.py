from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#kullanıcı kayıt formu
class KayitForm(Form):
    Adi = StringField('Ad-Soyad', [validators.Length(min=4, max=25)])
    KullaniciAdi = StringField('Kullanıcı Adı', [validators.Length(min=6, max=35)])
    Email= StringField('Email Adres', [validators.Length(min=6, max=35)])
    Parola = PasswordField('Yeni Parola', [
        validators.DataRequired(message="Parola Boş olamaz"),
        validators.EqualTo(fieldname="Dogrula")
    ])
    Dogrula=PasswordField("Parola Tekrar")
#Kullanıcı decarator ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "giris_yapildi" in session:
             return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntüleme izniniz yok","danger")
            return redirect(url_for("GirisYap"))
    return decorated_function
#Kullanıcı Giris Formu
class GirisForm(Form):
    KullaniciAdi=StringField("Kullanıcı Adı")
    Parola=PasswordField("Parola")
class MakaleForm(Form):
    Baslik=StringField("Makale Başlığı",validators=[validators.Length(min=5,max=50)])
    Icerik=TextAreaField("Makale İçerik",validators=[validators.Length(min=10)])
app=Flask(__name__)
app.secret_key="Flusk_Blog"#bunu yazmayınca flush mesajlarında hata veriyor
app.config["MYSQL_HOST"]="localhost"
#bunlar default degeler 
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="flask_blogdb"#veritabanı adı
app.config["MYSQL_CURSORCLASS"] = "DictCursor" #bu verilerin sözlük yapısında gelmesini sağlar
mysql=MySQL(app)
@app.route("/")
def index():
    return render_template("index.html",cevap="evet")
@app.route("/Hakkimizda")
def Hakkimizda():
    liste=[1,2,3]
    return render_template("Hakkimizda.html",liste=liste)
@app.route("/Makaleler")
def Makaleler():
    cursor=mysql.connection.cursor()
    sorgu="Select *from makale"
    sonuc= cursor.execute(sorgu)
    if(sonuc>0):
        makaleler=cursor.fetchall()
        return render_template("Makaleler.html",makaleler=makaleler)
    else:
        return render_template("Makaleler.html")
    
@app.route("/KayitOl",methods=["GET","POST"])#kayıt sayfası form içerdiği için belirttik
def KayitOl():
    form = KayitForm(request.form)
    if(request.method=="POST"and form.validate()):#form.validate() yukarıda yazdığımız kısıtlamalr gecerli ise 
      Adi=form.Adi.data
      KullaniciAdi=form.KullaniciAdi.data
      Email=form.Email.data
      Parola=sha256_crypt.encrypt(form.Parola.data) #veri tabanında şifrelenecek
      cursor=mysql.connection.cursor()
      sorgu="Insert into Kullanici(Adi,KullaniciAdi,Email,Parola) Values(%s,%s,%s,%s)"
      cursor.execute(sorgu,(Adi,KullaniciAdi,Email,Parola))
      mysql.connection.commit()#yaptıgımız değişikliği kaydet tarzında
      cursor.close()
      flash("Kayıt Başarılı..","success")
      return redirect(url_for("GirisYap"))
    else:
        return render_template("KayitOl.html",form=form)
@app.route("/GirisYap",methods=["Get","Post"])
def GirisYap():
    form=KayitForm(request.form)
    if(request.method=="POST"):
        KullaniciAdi=form.KullaniciAdi.data
        Parola=form.Parola.data
        cursor=mysql.connection.cursor()
        sorgu="SELECT * FROM kullanici WHERE KullaniciAdi=%s"
        result= cursor.execute(sorgu,(KullaniciAdi,))
        if(result>0):
            data=cursor.fetchone()
            gercek_parola=data["Parola"]
            if sha256_crypt.verify(Parola,gercek_parola):
                flash("Giriş Başarılı","success")
                session["giris_yapildi"]=True
                session["KullaniciAdi"]=KullaniciAdi

                return redirect(url_for("index"))
            else:
                flash("Kullanıcı adı veya parola yanlış","danger")
                return redirect(url_for("GirisYap"))
        else:
            flash("Kullanıcı Adı veya Parola Yanlış...","danger")
            return redirect(url_for("GirisYap"))
    else:
        return render_template("/GirisYap.html",form=form)
@app.route("/Kontrol_P")
@login_required
def Kontrol_P():
    cursor=mysql.connection.cursor()
    sorgu="Select * From makale where Yazar=%s"
    sonuc= cursor.execute(sorgu,(session["KullaniciAdi"],))
    if sonuc>0:
        makaleler=cursor.fetchall()
        return render_template("Kontrol_P.html",makaleler=makaleler)
    else:
        return render_template("Kontrol_P.html")

@app.route("/CikisYap")
def CikisYap():
     session.clear()
     return redirect(url_for("index"))
@app.route("/MakaleEkle",methods=["GET","POST"])
def MakaleEkle():
    form=MakaleForm(request.form)
    if(request.method=="POST"):
        Baslik=form.Baslik.data
        Icerik=form.Icerik.data
        cursor=mysql.connection.cursor()
        sorgu="Insert into Makale(Baslik,Icerik,Yazar) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(Baslik,Icerik,session["KullaniciAdi"]))
        mysql.connection.commit()
        cursor.close()
        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("Kontrol_P"))
    else:
        return render_template("MakaleEkle.html",form=form) 
@app.route("/Ara",methods=["GET","POST"])
def Ara():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        anahtarkelime=request.form.get("deger")
        cursor=mysql.connection.cursor()
        sorgu="Select * From makale where Baslik like '%"+anahtarkelime+"%'"
        sonuc=cursor.execute(sorgu)
        if sonuc>0:
            makaleler=cursor.fetchall()
            return render_template("Makaleler.html",makaleler=makaleler)
        else:
            flash("Aranan Kelimeye uygun Makale bulunamadı...","warning")
            return redirect(url_for("Makaleler"))
@app.route("/Article/<string:id>")
def detay(id):
    return "Detay id: "+id
@app.route("/Makale/<string:id>")
def MakaleDuzenle(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * From makale where id=%s"
    sonuc=cursor.execute(sorgu,(id,))
    if sonuc>0:
        makale=cursor.fetchone()
        return render_template("Makale.html",makale=makale)
    else:
        return render_template("/Makale.html")
@app.route("/Sil/<string:id>")
@login_required
def Sil(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * From makale where Yazar=%s and id=%s"
    sonuc=cursor.execute(sorgu,(session["KullaniciAdi"],id))
    if sonuc>0:
       sorgu2="Delete From makale where id=%s"
       cursor.execute(sorgu2,(id,))
       mysql.connection.commit()
       flash("Makale Başarılı bir şekilde silinmiştir","success")
       return redirect(url_for("Kontrol_P"))
    else:
        flash("Böyle bir makale yok veya silmeye yetkini yok","danger")
        return redirect("index")
@app.route("/Guncelle/<string:id>",methods=["GET","POST"])
@login_required
def Guncelle(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        sorgu="Select * From makale where Yazar=%s and id=%s"
        sonuc=cursor.execute(sorgu,(session["KullaniciAdi"],id))
        if sonuc>0:
            makale=cursor.fetchone()
            form=MakaleForm()
            form.Baslik.data=makale["Baslik"]
            form.Icerik.data=makale["Icerik"]
            return render_template("Guncelle.html",form=form)
        else:
            flash("Böyle bir makale yok veya yetkiniz yok")
            return redirect(url_for("Makaleler"))
    else:
        #post request
        form=MakaleForm(request.form)
        yenibaslik=form.Baslik.data
        yeniicerik=form.Icerik.data
        sorgu="Update makale set Baslik=%s,Icerik=%s where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu,(yenibaslik,yeniicerik,id))
        mysql.connection.commit()
        mysql.connection.close()
        flash("Makale Başarıyla Guncellendi","success")
        return redirect(url_for("Kontrol_P"))
if __name__=="__main__":
    app.run(debug=True)

