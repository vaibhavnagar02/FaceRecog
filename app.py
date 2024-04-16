from flask import Flask, render_template, request, redirect, url_for, flash
import face_recognition
import os
from flask import send_from_directory
 


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    app.config['UPLOAD_FOLDER'] = 'uploads'

    from models import db
    db.init_app(app)

    @app.route('/')
    def index():
        return render_template('index.html')


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            image = request.files.get('image')

            if not username or not image:
                flash('Username and image are required!')
                return redirect(url_for('register'))

            # Check if the directory exists, if not, create it
            if not os.path.exists('uploads'):
                os.mkdir('uploads')

            image_path = os.path.join('uploads', image.filename)
            image.save(image_path)

            image_to_encode = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image_to_encode)

            if not face_encodings:
                flash('Cannot detect a face in the image!')
                return redirect(url_for('register'))

            new_user = User(username=username, face_encoding=face_encodings[0])
            db.session.add(new_user)
            db.session.commit()

            flash('Registered successfully!')
            return redirect(url_for('index'))

        return render_template('register.html')


    @app.route('/recognize', methods=['GET', 'POST'])
    def recognize():
        if request.method == 'POST':
            image = request.files.get('image')
            if not image:
                flash('Image is required!')
                return redirect(url_for('recognize'))

            image_path = os.path.join('uploads', image.filename)
            image.save(image_path)

            unknown_image = face_recognition.load_image_file(image_path)
            unknown_face_encodings = face_recognition.face_encodings(unknown_image)

            if not unknown_face_encodings:
                flash('Cannot detect a face in the image!')
                return redirect(url_for('recognize'))

            recognized_users = []
            all_users = User.query.all()
            similarity_percentages = []
            for user in all_users:
                match = face_recognition.compare_faces([user.face_encoding], unknown_face_encodings[0])
                if match[0]:
                    distance = face_recognition.face_distance([user.face_encoding], unknown_face_encodings[0])
                    similarity_percentage = (1 - distance) * 100
                    photo_path = url_for('uploaded_file', filename=image.filename)
                    recognized_users.append((user.username, similarity_percentage, image_path))


            if recognized_users:
                return render_template('recognized.html', recognized_users=recognized_users)
            else:
                return render_template('False_recognized.html')

        return render_template('recognize.html')

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/database')
    def database():
        all_users = User.query.all()
        return render_template('database.html', users=all_users)


    @app.route('/delete/<int:user_id>', methods=['POST'])
    def delete_user(user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!')
        return redirect(url_for('database'))

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        from models import db, User
        db.create_all()
    app.run(debug=True, port=8000)
