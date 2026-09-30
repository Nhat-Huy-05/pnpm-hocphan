from flask import Flask, render_template, request

app = Flask(__name__, template_folder="../templates")


@app.route('/', methods=['GET', 'POST'])
def home():
    a = request.form.get("a")
    b = request.form.get("b")

    try:
        num_a = float(a) if a not in (None, "") else 0.0
        num_b = float(b) if b not in (None, "") else 0.0
    except ValueError:
        num_a = 0.0
        num_b = 0.0

    ketqua = {
        'cong': num_a + num_b,
        'tru': num_a - num_b,
        'nhan': num_a * num_b,
        'chia': num_a / num_b if num_b != 0 else "Không thể chia cho 0"
    }

    return render_template("math.html", a=a, b=b, ketqua=ketqua)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True) 