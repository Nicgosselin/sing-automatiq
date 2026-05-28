import asyncio
import csv
import re
from playwright.async_api import async_playwright

VILLES = ["Québec", "Lévis", "Trois-Rivières", "Drummondville", "Saint-Georges"]
METIERS = ["entrepreneur rénovation", "entrepreneur général", "plombier", "électricien"]

async def chercher_email(browser, url):
    page = await browser.new_page()
    try:
        await page.goto(url, timeout=8000, wait_until="domcontentloaded")
        contenu = await page.content()
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', contenu)
        emails = [e for e in emails if not any(x in e for x in ['exemple','example','domain','png','jpg','svg','woff'])]
        return emails[0] if emails else None
    except:
        return None
    finally:
        await page.close()

async def scraper_maps(browser, query):
    page = await browser.new_page()
    resultats = []
    try:
        await page.goto(f"https://www.google.com/maps/search/{query.replace(' ', '+')}", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        items = await page.query_selector_all('a[href*="/maps/place/"]')
        liens = list(set([await i.get_attribute('href') for i in items[:10]]))
        
        for lien in liens[:5]:
            try:
                await page.goto(lien, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                
                nom = await page.title()
                
                site_btn = await page.query_selector('a[data-item-id="authority"]')
                site = await site_btn.get_attribute('href') if site_btn else None
                
                tel_el = await page.query_selector('button[data-item-id*="phone"]')
                tel = await tel_el.inner_text() if tel_el else None
                
                email = None
                if site:
                    email = await chercher_email(browser, site)
                
                if tel or email:
                    resultats.append({
                        'nom': nom.replace(' - Google Maps', ''),
                        'telephone': tel,
                        'email': email,
                        'site': site,
                        'query': query
                    })
                    print(f"✅ {nom[:50]} | {tel} | {email}")
            except:
                continue
    except Exception as e:
        print(f"⚠️ Erreur: {e}")
    finally:
        await page.close()
    
    return resultats

async def main():
    tous = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for ville in VILLES:
            for metier in METIERS:
                query = f"{metier} {ville} Québec"
                print(f"\n🔍 {query}")
                r = await scraper_maps(browser, query)
                tous.extend(r)
        
        await browser.close()
    
    # Déduplique par email
    seen = set()
    uniques = []
    for c in tous:
        key = c.get('email') or c.get('telephone')
        if key and key not in seen:
            seen.add(key)
            uniques.append(c)
    
    with open('contacts.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['nom','telephone','email','site','query'])
        writer.writeheader()
        writer.writerows(uniques)
    
    print(f"\n✅ {len(uniques)} contacts uniques sauvegardés dans contacts.csv")

asyncio.run(main())
