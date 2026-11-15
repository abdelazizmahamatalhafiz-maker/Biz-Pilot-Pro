import os, hashlib
from datetime import date, datetime
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Biz-Pilot Pro", page_icon="🚀", layout="wide")
st.markdown("""<style>div[data-testid="metric-container"]{background-color:#1E293B;border:1px solid #334155;padding:15px 20px;border-radius:12px;}.receipt-box{background-color:#FFFFFF;color:#0F172A;padding:25px;border-radius:10px;border:2px dashed #94A3B8;font-family:'Courier New',monospace;}</style>""", unsafe_allow_html=True)

FICHIER_VENTES = "ventes_boutique.csv"
MOT_DE_PASSE_HASH = hashlib.sha256("admin123".encode()).hexdigest()

if "authentifie" not in st.session_state:
    st.session_state.authentifie = False

if not st.session_state.authentifie:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.title("🚀 Biz-Pilot Pro")
        st.caption("Solution intelligente de gestion de caisse, stock et facturation.")
        with st.form("login_form"):
            mdp = st.text_input("Mot de passe d'accès", type="password", placeholder="admin123")
            if st.form_submit_button("Accéder au tableau de bord", use_container_width=True):
                if hashlib.sha256(mdp.encode()).hexdigest() == MOT_DE_PASSE_HASH:
                    st.session_state.authentifie = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect.")
    st.stop()

def charger_donnees():
    cols = ["ID", "Date", "Caisse", "Type", "Produit", "Client", "Quantite", "Prix_Vente", "Cout_Achat"]
    if os.path.exists(FICHIER_VENTES):
        df = pd.read_csv(FICHIER_VENTES)
        if "ID" not in df.columns: df["ID"] = [f"TRX-{1000+i}" for i in range(len(df))]
        if "Type" not in df.columns: df["Type"] = "Entrée (+)"
        if "Client" not in df.columns: df["Client"] = "Client Comptoir"
        if "Caisse" not in df.columns: df["Caisse"] = "Boutique"
        return df[cols]
    return pd.DataFrame(columns=cols)

def ajouter_operation(v_date, caisse, op_type, produit, client, quantite, prix, cout):
    df = charger_donnees()
    trx_id = f"TRX-{datetime.now().strftime('%H%M%S')}"
    new_row = pd.DataFrame([{"ID": trx_id, "Date": str(v_date), "Caisse": caisse, "Type": op_type, "Produit": produit.strip(), "Client": client.strip() or "Client Comptoir", "Quantite": int(quantite), "Prix_Vente": float(prix), "Cout_Achat": float(cout)}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(FICHIER_VENTES, index=False)
    return trx_id

top1, top2 = st.columns([4, 1])
with top1:
    st.title("🚀 Biz-Pilot Pro")
    st.caption("Plateforme de gestion commerciale & suivi multi-caisses en temps réel")
with top2:
    if st.button("🔒 Déconnexion", use_container_width=True):
        st.session_state.authentifie = False
        st.rerun()

df = charger_donnees()
if not df.empty:
    df["Montant_Total"] = df.apply(lambda r: (r["Quantite"] * r["Prix_Vente"]) if r["Type"] == "Entrée (+)" else -(r["Quantite"] * r["Prix_Vente"]), axis=1)
    df["Benefice_Net"] = df.apply(lambda r: ((r["Quantite"] * r["Prix_Vente"]) - (r["Quantite"] * r["Cout_Achat"])) if (r["Caisse"] == "Boutique" and r["Type"] == "Entrée (+)") else (r["Montant_Total"] if r["Type"] == "Sortie (-)" and r["Caisse"] == "Boutique" else 0), axis=1)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Tableau de Bord", "➕ Nouvelle Opération", "🧾 Reçu Client", "⚙️ Gestion & Export"])

with tab1:
    if df.empty:
        st.info("👋 Bienvenue sur Biz-Pilot Pro ! Cliquez sur l'onglet **➕ Nouvelle Opération** pour enregistrer votre première vente.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🏪 Caisse Boutique", f"{df[df['Caisse']=='Boutique']['Montant_Total'].sum():,.0f} FCFA".replace(",", " "))
        m2.metric("💰 Bénéfice Net Réel", f"{df[df['Caisse']=='Boutique']['Benefice_Net'].sum():,.0f} FCFA".replace(",", " "))
        m3.metric("👤 Argent Personnel", f"{df[df['Caisse']=='Argent Personnel']['Montant_Total'].sum():,.0f} FCFA".replace(",", " "))
        m4.metric("🤝 Dépôts Clients", f"{df[df['Caisse']=='Dépôt Client']['Montant_Total'].sum():,.0f} FCFA".replace(",", " "))

        filtre = st.selectbox("Filtrer l'affichage :", ["Toutes les caisses", "Boutique", "Argent Personnel", "Dépôt Client"])
        df_aff = df if filtre == "Toutes les caisses" else df[df["Caisse"] == filtre]

        g1, g2 = st.columns(2)
        with g1:
            st.subheader("🏆 Performance par Produit / Service")
            vp = df_aff[df_aff["Type"] == "Entrée (+)"]
            if not vp.empty: st.bar_chart(vp.groupby("Produit")["Montant_Total"].sum(), color="#2563EB")
        with g2:
            st.subheader("📈 Évolution de la Trésorerie")
            st.line_chart(df_aff.groupby("Date")["Montant_Total"].sum(), color="#10B981")

        st.subheader("📋 Dernières transactions")
        st.dataframe(df_aff.iloc[::-1], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Enregistrer une vente, une dépense ou un dépôt")
    with st.form("form_dyn", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        op_date = c1.date_input("Date", value=date.today())
        op_caisse = c1.selectbox("Caisse", ["Boutique", "Argent Personnel", "Dépôt Client"])
        op_type = c2.selectbox("Type", ["Entrée (+)", "Sortie (-)"])
        op_prod = c2.text_input("Article, Service ou Motif", placeholder="Ex: Flash Samsung A14")
        op_client = c3.text_input("Client (optionnel)", placeholder="Ex: Moussa")
        op_qty = c3.number_input("Quantité", min_value=1, value=1)
        p1, p2 = st.columns(2)
        op_prix = p1.number_input("Prix unitaire / Montant (FCFA)", min_value=0, value=5000, step=500)
        op_cout = p2.number_input("Coût d'achat unitaire (0 si service)", min_value=0, value=0, step=500)

        if st.form_submit_button("✅ Valider et enregistrer", use_container_width=True):
            if not op_prod.strip(): st.error("Veuillez indiquer le nom de l'article.")
            else:
                nid = ajouter_operation(op_date, op_caisse, op_type, op_prod, op_client, op_qty, op_prix, op_cout)
                st.success(f"Opération **{nid}** enregistrée dans **{op_caisse}** !")

with tab3:
    st.subheader("🧾 Générer un reçu professionnel pour un client")
    if df.empty:
        st.info("Enregistrez d'abord une vente pour générer un reçu.")
    else:
        nom_b = st.text_input("Nom de la boutique", value="BOUTIQUE PHONE & SERVICES")
        tel_b = st.text_input("Téléphone", value="66 02 15 37")
        liste_trx = df["ID"] + " - " + df["Produit"] + " (" + df["Client"] + ")"
        choix = st.selectbox("Transaction :", liste_trx.iloc[::-1])
        ligne = df[df["ID"] == choix.split(" - ")[0]].iloc[0]
        tot = ligne["Quantite"] * ligne["Prix_Vente"]
        st.markdown(f"""<div class="receipt-box"><h3 style="text-align:center;margin-bottom:5px;">{nom_b}</h3><p style="text-align:center;margin-top:0;">Tél : {tel_b}</p><hr><p><strong>Reçu N° :</strong> {ligne['ID']}</p><p><strong>Date :</strong> {ligne['Date']}</p><p><strong>Client :</strong> {ligne['Client']}</p><hr><p><strong>Désignation :</strong> {ligne['Produit']} (x{ligne['Quantite']})</p><p><strong>Prix Unitaire :</strong> {ligne['Prix_Vente']:,.0f} FCFA</p><h3 style="text-align:right;">TOTAL PAYÉ : {tot:,.0f} FCFA</h3><hr><p style="text-align:center;font-size:12px;">Merci pour votre confiance ! Document généré par Biz-Pilot Pro.</p></div>""", unsafe_allow_html=True)

with tab4:
    st.subheader("⚙️ Administration et Sauvegarde")
    if not df.empty:
        csv_exp = df.drop(columns=["Montant_Total", "Benefice_Net"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Télécharger la sauvegarde (CSV)", data=csv_exp, file_name=f"BizPilot_Backup_{date.today()}.csv", mime="text/csv")
        if st.button("🗑️ Annuler la dernière opération"):
            df.drop(columns=["Montant_Total", "Benefice_Net"], errors="ignore").iloc[:-1].to_csv(FICHIER_VENTES, index=False)
            st.success("Dernière opération supprimée.")
            st.rerun()
