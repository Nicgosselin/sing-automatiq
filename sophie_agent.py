import subprocess
import asyncio
import whisper
import requests
import json
import os
import tempfile

# Config
OLLAMA_URL = "http://localhost:11434/api/generate"
VOICE = "fr-CA-SylvieNeural"
WHISPER_MODEL = None

def init_whisper():
    global WHISPER_MODEL
    print("🧠 Chargement Whisper...")
    WHISPER_MODEL = whisper.load_model("small", device="cpu")
    print("✅ Whisper prêt")

def sophie_pense(conversation):
    """Envoie la conversation à Sophie et retourne sa réponse"""
    messages = "\n".join([f"{m['role']}: {m['content']}" for m in conversation])
    
    response = requests.post(OLLAMA_URL, json={
        "model": "sophie",
        "prompt": messages + "\nsophie:",
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 150}
    })
    
    return response.json()["response"].strip()

async def sophie_parle(texte, fichier_sortie):
    """Convertit le texte en voix avec Sophie"""
    proc = await asyncio.create_subprocess_exec(
        "edge-tts",
        "--voice", VOICE,
        "--text", texte,
        "--write-media", fichier_sortie,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()

def tremblay_parle(fichier_audio):
    """Transcrit la réponse de Tremblay"""
    result = WHISPER_MODEL.transcribe(
        fichier_audio,
        initial_prompt="SING Automatiq AgentPME Nicolas Gosselin Québec entrepreneur rénovation",
        language="fr"
    )
    return result["text"].strip()

def joue_audio(fichier):
    """Joue le fichier audio"""
    subprocess.run(["mpv", "--really-quiet", fichier])

def enregistre_micro(fichier_sortie, duree=5):
    """Enregistre depuis le micro"""
    subprocess.run([
        "arecord", "-f", "S16_LE", "-r", "16000",
        "-d", str(duree), fichier_sortie
    ], capture_output=True)

async def appel_simulation(nom_contact, telephone):
    """Simule un appel complet avec Sophie"""
    print(f"\n{'='*50}")
    print(f"📞 Appel simulé : {nom_contact} — {telephone}")
    print(f"{'='*50}\n")

    conversation = [{
        "role": "contexte",
        "content": f"Tu appelles {nom_contact} au {telephone}. C'est ton premier contact avec eux."
    }]

    # Sophie ouvre l'appel
    ouverture = sophie_pense(conversation + [{"role": "instruction", "content": "Ouvre l'appel avec une salutation naturelle et présente-toi."}])
    print(f"🤖 Sophie : {ouverture}\n")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        audio_sophie = f.name

    await sophie_parle(ouverture, audio_sophie)
    joue_audio(audio_sophie)
    conversation.append({"role": "sophie", "content": ouverture})

    # Boucle de conversation
    tour = 0
    while tour < 5:
        tour += 1
        print("🎤 Votre réponse (appuyez Entrée pour simuler une réponse)...")
        
        # Mode test : saisie clavier
        reponse_tremblay = input("Tremblay dit : ").strip()
        
        if not reponse_tremblay or reponse_tremblay.lower() in ["bye", "au revoir", "non merci"]:
            print("\n📵 Fin de l'appel")
            break

        conversation.append({"role": "prospect", "content": reponse_tremblay})

        # Sophie réfléchit et répond
        print("💭 Sophie réfléchit...")
        reponse_sophie = sophie_pense(conversation)
        print(f"🤖 Sophie : {reponse_sophie}\n")

        await sophie_parle(reponse_sophie, audio_sophie)
        joue_audio(audio_sophie)
        conversation.append({"role": "sophie", "content": reponse_sophie})

    os.unlink(audio_sophie)
    print(f"\n✅ Appel terminé — {tour} échanges")
    return conversation

async def main():
    init_whisper()
    
    # Test avec un contact fictif
    await appel_simulation(
        nom_contact="Construction Tremblay",
        telephone="418-555-0123"
    )

if __name__ == "__main__":
    asyncio.run(main())
