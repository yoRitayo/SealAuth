# Sem SMTP_HOST configurado, cai no modo de desenvolvimento: registra o link no log
# em vez de enviar, para permitir testar os fluxos sem um servidor de e-mail real.
import html
import logging
import smtplib
from email.message import EmailMessage

from config import (
    AMBIENTE,
    FRONTEND_URL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_REMETENTE,
    SMTP_SENHA,
    SMTP_USER,
)

logger = logging.getLogger("sealauth.email")

# Paleta do logo do SealAuth. gradiente blue-600 -> indigo-600
COR_INICIO = "#2563eb"
COR_FIM = "#4f46e5"
COR_TEXTO = "#1f2937"
COR_SECUNDARIA = "#6b7280"


def _html_email(
    titulo: str, paragrafos: list[str], texto_botao: str, link: str, rodape: str
) -> str:
    corpo = "".join(
        f'<p style="margin:0 0 16px 0;font-size:16px;line-height:24px;color:{COR_TEXTO};">{html.escape(p)}</p>'
        for p in paragrafos
    )
    logo_url = f"{FRONTEND_URL.rstrip('/')}/seal-icon72.png"
    gradiente = f"linear-gradient(135deg,{COR_INICIO},{COR_FIM})"
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f1f5f9;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:480px;background-color:#ffffff;border-radius:16px;">
          <tr>
            <td align="center" style="padding:32px 32px 8px 32px;">
              <table role="presentation" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="background:{gradiente};background-color:{COR_INICIO};border-radius:12px;width:40px;height:40px;text-align:center;vertical-align:middle;">
                    <img src="{html.escape(logo_url)}" width="24" height="24" alt="Ícone do SealAuth" style="display:inline-block;border:0;vertical-align:middle;" />
                  </td>
                  <td style="padding-left:8px;font-size:24px;font-weight:bold;color:{COR_FIM};">SealAuth</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 32px 0 32px;">
              <h1 style="margin:0 0 16px 0;font-size:22px;line-height:30px;color:{COR_TEXTO};">{html.escape(titulo)}</h1>
              {corpo}
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:8px 32px 24px 32px;">
              <a href="{html.escape(link)}" style="display:inline-block;background:{gradiente};background-color:{COR_INICIO};color:#ffffff;text-decoration:none;font-weight:bold;font-size:16px;padding:14px 28px;border-radius:12px;">{html.escape(texto_botao)}</a>
              <p style="margin:20px 0 0 0;font-size:13px;line-height:20px;color:{COR_SECUNDARIA};">
                Se o botão não funcionar, copie e cole este link no navegador:<br />
                <span style="word-break:break-all;color:{COR_INICIO};">{html.escape(link)}</span>
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 32px 32px 32px;border-top:1px solid #e5e7eb;">
              <p style="margin:0;font-size:12px;line-height:18px;color:{COR_SECUNDARIA};">{html.escape(rodape)}</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def enviar_email(
    destinatario: str, assunto: str, corpo: str, html_corpo: str | None = None
) -> None:
    if not SMTP_HOST:
        if AMBIENTE != "development":
            raise RuntimeError(
                "SMTP_HOST não configurado fora do ambiente de desenvolvimento (ENV != 'development')"
            )
        logger.warning(
            "SMTP_HOST não configurado; e-mail não enviado (você está em modo desenvolvimento).\n"
            "Para: %s | Assunto: %s\n%s",
            destinatario,
            assunto,
            corpo,
        )
        return

    mensagem = EmailMessage()
    mensagem["From"] = SMTP_REMETENTE
    mensagem["To"] = destinatario
    mensagem["Subject"] = assunto
    mensagem.set_content(corpo)  # texto puro: fallback para clientes sem HTML
    if html_corpo:
        mensagem.add_alternative(html_corpo, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as servidor:
        servidor.starttls()
        if SMTP_USER:
            servidor.login(SMTP_USER, SMTP_SENHA)
        servidor.send_message(mensagem)


def enviar_email_ativacao(destinatario: str, link: str) -> None:
    titulo = "Ative sua conta"
    paragrafos = ["Bem-vindo ao SealAuth! Confirme seu e-mail para ativar sua conta."]
    rodape = "Se você não criou esta conta, ignore esta mensagem."
    enviar_email(
        destinatario,
        "Ative sua conta no SealAuth",
        f"{titulo}\n\n{paragrafos[0]}\n\n{link}\n\n{rodape}",
        _html_email(titulo, paragrafos, "Ativar minha conta", link, rodape),
    )


def enviar_email_redefinicao(destinatario: str, link: str) -> None:
    titulo = "Redefinição de senha"
    paragrafos = [
        "Recebemos um pedido de redefinição de senha. Clique no botão abaixo para escolher uma nova senha.",
        "Este link expira em breve e só pode ser usado uma vez.",
    ]
    rodape = (
        "Se você não solicitou isso, entre em contato com o suporte técnico do serviço"
    )
    enviar_email(
        destinatario,
        "Redefinição de senha no SealAuth",
        f"{titulo}\n\n{paragrafos[0]}\n{paragrafos[1]}\n\n{link}\n\n{rodape}",
        _html_email(titulo, paragrafos, "Redefinir minha senha", link, rodape),
    )
