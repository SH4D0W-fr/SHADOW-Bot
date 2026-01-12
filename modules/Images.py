def GenerateWelcomeImage(username: str) -> str:
    model = f"assets/welcome-image-model.png"
    output = f"temp/welcome-{username}.png"
    