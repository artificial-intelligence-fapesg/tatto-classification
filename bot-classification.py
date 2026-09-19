import io
import os
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

from BuildModel import build_model
from database import Tatuador, buscar_por_classe, criar_schema, listar_todos

# ---- Configurações ----
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_PATH = "models/tattogyn1.weights.h5"
IMG_SIZE = (224, 224)  # ajuste ao tamanho esperado pelo seu modelo
CLASSES = ['anabele', 'chris', 'manuela', 'matheus', 'michel', 'pablo']  # ajuste às suas classes
CONFIANCA_MINIMA = 0.60  # abaixo disso o bot avisa que não tem certeza

criar_schema()
model = build_model()
model.load_weights(MODEL_PATH)

print("Modelo carregado com sucesso!")


def preprocess(img: Image.Image) -> np.ndarray:
    img = img.convert("RGB").resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


# ---- Formatação da resposta ----

def escapar(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def montar_ficha(t: Tatuador, confianca: float) -> str:
    linhas = [f"<b>{escapar(t.nome)}</b>"]
    if t.apelido:
        linhas.append(f"<i>{escapar(t.apelido)}</i>")
    linhas.append(f"Confiança da classificação: {confianca:.1%}")

    if t.bio:
        linhas += ["", escapar(t.bio)]
    if t.especialidades:
        linhas.append(f"\n🎨 <b>Estilos:</b> {escapar(t.especialidades)}")

    endereco = t.endereco_completo
    if t.estudio or endereco:
        linhas.append("\n📍 <b>Onde encontrar</b>")
        if t.estudio:
            linhas.append(escapar(t.estudio))
        if endereco:
            linhas.append(escapar(endereco))
        if t.horario:
            linhas.append(f"🕐 {escapar(t.horario)}")

    if any([t.telefone, t.whatsapp, t.email]):
        linhas.append("\n📞 <b>Contato</b>")
        if t.telefone:
            linhas.append(f"Telefone: {escapar(t.telefone)}")
        if t.whatsapp:
            linhas.append(f"WhatsApp: https://wa.me/{t.whatsapp}")
        if t.email:
            linhas.append(f"E-mail: {escapar(t.email)}")

    if any([t.instagram, t.tiktok, t.facebook, t.site]):
        linhas.append("\n🌐 <b>Redes</b>")
        if t.instagram:
            linhas.append(f"Instagram: https://instagram.com/{t.instagram}")
        if t.tiktok:
            linhas.append(f"TikTok: https://tiktok.com/@{t.tiktok}")
        if t.facebook:
            linhas.append(f"Facebook: https://facebook.com/{t.facebook}")
        if t.site:
            linhas.append(f"Site: {escapar(t.site)}")

    if t.preco_medio:
        linhas.append(f"\n💰 {escapar(t.preco_medio)}")

    return "\n".join(linhas)


def montar_botoes(t: Tatuador) -> InlineKeyboardMarkup | None:
    botoes = []
    if t.whatsapp:
        botoes.append(InlineKeyboardButton("WhatsApp", url=f"https://wa.me/{t.whatsapp}"))
    if t.instagram:
        botoes.append(InlineKeyboardButton("Instagram", url=f"https://instagram.com/{t.instagram}"))
    if t.site:
        botoes.append(InlineKeyboardButton("Site", url=t.site))
    if t.tem_coordenadas:
        botoes.append(InlineKeyboardButton(
            "Abrir no mapa",
            url=f"https://www.google.com/maps/search/?api=1&query={t.latitude},{t.longitude}",
        ))
    if not botoes:
        return None
    # 2 botões por linha
    linhas = [botoes[i:i + 2] for i in range(0, len(botoes), 2)]
    return InlineKeyboardMarkup(linhas)


# ---- Handlers ----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Envie a foto de uma tatuagem e eu digo qual tatuador fez, "
        "com contato, redes e localização do estúdio.\n\n"
        "/tatuadores — lista todos os tatuadores cadastrados"
    )


async def tatuadores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    todos = listar_todos()
    if not todos:
        await update.message.reply_text("Nenhum tatuador cadastrado ainda.")
        return
    texto = "\n".join(
        f"• {t.nome}" + (f" — {t.estudio}" if t.estudio else "") for t in todos
    )
    await update.message.reply_text(f"Tatuadores cadastrados:\n{texto}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    img = Image.open(io.BytesIO(photo_bytes))

    x = preprocess(img)
    preds = model.predict(x)[0]
    idx = int(np.argmax(preds))
    conf = float(preds[idx])
    classe = CLASSES[idx] if idx < len(CLASSES) else str(idx)

    if conf < CONFIANCA_MINIMA:
        await update.message.reply_text(
            f"Não consegui identificar com segurança.\n"
            f"Palpite: {classe} ({conf:.1%}). Tente uma foto mais nítida e enquadrada."
        )
        return

    tatuador = buscar_por_classe(classe)
    if tatuador is None:
        await update.message.reply_text(
            f"Classe: {classe}\nConfiança: {conf:.1%}\n\n"
            "(Esse tatuador ainda não está cadastrado no banco.)"
        )
        return

    await update.message.reply_text(
        montar_ficha(tatuador, conf),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=montar_botoes(tatuador),
    )

    if tatuador.tem_coordenadas:
        await update.message.reply_location(
            latitude=tatuador.latitude,
            longitude=tatuador.longitude,
        )


def main():
    app = ApplicationBuilder().token(TOKEN).connect_timeout(30).read_timeout(30).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tatuadores", tatuadores))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()


if __name__ == "__main__":
    main()