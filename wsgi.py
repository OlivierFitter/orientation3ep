from app import create_app, db

app = create_app()

# Créer les tables si elles n'existent pas encore
# (filet de sécurité si flask db upgrade n'a pas tourné)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False)
