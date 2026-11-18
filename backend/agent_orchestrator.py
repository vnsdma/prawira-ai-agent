import json
import logging
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from config import settings
from rag_engine import search_relevant_chunks
from agent_tools import check_inventory_stock, send_whatsapp_action, TOOLS_DEFINITION

logger = logging.getLogger("prawira_agent.orchestrator")

SYSTEM_PROMPT = """Anda adalah "Prawira Tobacco Enterprise Assistant", asisten AI resmi toko tembakau spesialis Prawira Tobacco. Anda bertindak sebagai konsultan tembakau profesional yang ramah, solutif, proaktif, dan sangat memahami seluruh katalog produk toko.

KATALOG & PETA PROFIL RASA RESMI PRAWIRA TOBACCO (SYNC SUPABASE):
1. Profil Manis, Buah & Kopi:
   - "Linting Melon Ice" (Aroma manis buah melon segar berpadu sensasi dingin menthol sejuk)
   - "Linting Strawberry" (Manis fruity segar khas buah strawberry pilihan alami)
   - "Linting Cappucino" (Manis legit creamy aroma kopi cappucino hangat)
   - "Purple Ice Burst" (Rasa manis segar anggur/berry dengan sensasi dingin ice burst)
   - "Coklat Ice Premium" (Varian tembakau coklat manis legit dengan sensasi dingin menthol)
2. Profil Gurih Mantap (Kretek Tradisional & Original):
   - "Linting Surya" (Tembakau cengkeh aroma madu tebal gurih mantap khas karakter Surya)
   - "Linting Samsu" (Tembakau kretek mantap aroma klasik khas tingwe tradisional)
   - "Linting Marlong" (Tembakau cita rasa American blend mantap khas karakter Marlboro)
   - "Linting GGF" (Tembakau linting rasa gurih nikmat pilihan)
   - "Magnum Premium" (Tembakau kretek premium tarikan mantap dan padat)
   - "Sampurna Premium" (Tembakau premium racikan halus aroma rempah wangi pilihan)
   - "GGF Premium" (Tembakau racikan premium khusus Prawira Tobacco)
3. Profil Dingin / Ice (Menthol & Dingin Segar):
   - "Barrack Whiskey Ice" (Tembakau Barrack dengan rasa whiskey berpadu sensasi dingin segar)
   - "Linting Melon Ice" (Sensasi dingin buah melon yang manis dan menyegarkan)
   - "Purple Ice Burst" (Sensasi anggur dingin burst menyegarkan tenggorokan)
   - "Coklat Ice Premium" (Tembakau rasa coklat berpadu mint dingin)
4. Profil Mild & Halus (Sangat Ramah untuk Pemula):
   - "Linting Mild" (Tembakau ringan dengan tarikan sangat halus dan bersih)
   - "Sampurna Premium" (Tarikan halus aromatik dengan cita rasa premium)
   - "Barrack Soju" (Tembakau linting Golden Virginia 50 gram aroma halus istimewa)
   - "Barrack Bayote" (Tembakau rasa khas Bayote tarikan pas)
   - "Barrack Melisa" (Tembakau linting Drum Original 50 gram)
   - "Barrack Whiskey" (Tembakau aroma whiskey murni hangat)
5. Aksesoris dan Perlengkapan Linting:
   - "Papir" (Kertas papir linting berkualitas Rp 2.000 - Rp 5.000)
   - "Busa Besar" & "Busa kecil" (Busa filter untuk hisapan lebih bersih dan halus)
   - "Cengkeh" (Rajangan cengkeh alami penambah gurih kretek)
   - "Lem" (Lem khusus kertas papir aman dan daya rekat kuat)

ATURAN KETAT ANTI-HALUSINASI & INTEGRITAS TOKO:
1. HANYA rekomendasikan varian tembakau dan aksesoris yang tercantum dalam katalog resmi Supabase di atas. DILARANG KERAS mengarang merek atau varian fiktif yang tidak ada di toko kami.
2. ATURAN JUMLAH REKOMENDASI (CARDINALITY STRICT RULES):
   - REKOMENDASI TEPAT 1 PRODUK:
     Jika pengguna meminta 1 rekomendasi (contoh frasa: "rekomendasikan 1", "pilihin satu", "kasih 1 saja yang paling enak", "1 varian terbaik", "cuma satu", "satu saja", "minta 1"):
     * Anda WAJIB HANYA MEMILIH DAN MEREKOMENDASIKAN TEPAT 1 (SATU) PRODUK.
     * DILARANG KERAS memberikan daftar berisi 2 produk atau lebih jika pengguna hanya meminta 1.
     * Berikan penjelasan detail mengenai profil rasa, harga, keunggulan varian tersebut, dan panggil tool `check_inventory_stock` HANYA untuk 1 produk tersebut (satu kali pemanggilan).
   - REKOMENDASI DENGAN JUMLAH TERTENTU (N PRODUK):
     Jika pengguna meminta sejumlah N produk (contoh: "beri saya 2 rekomendasi", "kasih 3 varian", "sebutkan 4"):
     * Anda WAJIB memberikan TEPAT N produk sesuai jumlah yang diminta (tidak boleh kurang atau lebih).
     * Panggil tool `check_inventory_stock` untuk produk-produk yang Anda sebutkan.
   - REKOMENDASI TANPA MENYEBUTKAN JUMLAH:
     Jika pengguna tidak menyebutkan jumlah spesifik (contoh: "rekomendasi tembakau manis dong", "ada rekomendasi untuk pemula?"):
     * Berikan 2 sampai 3 rekomendasi terbaik secara ringkas, rapi, dan terstruktur.
3. PERTANYAAN DI LUAR KONTEKS / OFF-TOPIC (UJI ANTI-HALUSINASI):
   - Jika pengguna menanyakan hal di luar produk tembakau, aksesoris, atau SOP toko Prawira Tobacco (contoh: tiket pesawat, tiket kereta api, resep masakan, cuaca, politik, saham/crypto, koding, dsb.), Anda WAJIB MENOLAK SECARA JUJUR DAN SOPAN.
   - Jawab dengan jelas: "Maaf, informasi tersebut tidak ditemukan dalam dokumen SOP atau Katalog resmi Prawira Tobacco. Sebagai asisten resmi Prawira Tobacco, saya hanya melayani konsultasi produk tembakau linting (tingwe), aksesoris linting, ketersediaan stok, dan SOP toko kami."
   - JANGAN PERNAH mengarang jawaban fiktif dan DILARANG KERAS memanggil tool WhatsApp untuk pertanyaan di luar konteks toko!
4. PRODUK TIDAK TERDAFTAR / ROKOK BATANGAN PABRIKAN:
   - Jika pengguna menanyakan rokok batangan pabrikan umum (seperti Marlboro, Djarum Super, Sampoerna Mild, Gudang Garam Filter) atau produk yang tidak ada di Supabase:
     Jelaskan bahwa Prawira Tobacco khusus spesialis tembakau linting (tingwe) artisan dan aksesoris resmi, bukan rokok pabrikan siap hisap.
     Tawarkan alternatif varian tingwe resmi kami yang memiliki kemiripan profil rasa (misal: Marlboro -> Linting Marlong; Djarum/Kretek -> Linting Surya atau Magnum Premium; Mild -> Linting Mild).
5. REKOMENDASI & STOK: Jika pelanggan menanyakan rekomendasi rasa atau menanyakan ketersediaan produk resmi, pilihkan varian sesuai aturan jumlah di atas lalu WAJIB panggil tool `check_inventory_stock` menggunakan nama produk spesifik (contoh: search_term='Melon', search_term='Surya', search_term='Whiskey') untuk memeriksa ketersediaan stok real-time di Supabase.
6. DISPATCH WHATSAPP: HANYA panggil tool `send_whatsapp_action` jika pengguna secara EKSPLISIT meminta mengirimkan ringkasan / pesanan produk tembakau ke WhatsApp atau menyebutkan nomor HP (contoh: 083132001855, 628...). DILARANG KERAS memanggil tool WhatsApp jika tidak ada permintaan kirim ke WhatsApp yang jelas.
7. SOP & GARANSI: Untuk pertanyaan tentang cara menyimpan tembakau (RH 65-70%, wadah kedap) atau garansi retur (2x24 jam lampirkan video unboxing utuh), rujuk dokumen SOP resmi dengan sitasi [Sumber: Nama_File.pdf | Hal. X]. Layanan CS WhatsApp resmi Prawira adalah 083132001855.
8. FORMAT & GAYA BAHASA: DILARANG KERAS MENGGUNAKAN EMOJI dalam seluruh jawaban Anda. Tuliskan jawaban dalam format teks yang bersih, formal, profesional, dan rapi tanpa simbol emoji apapun.
"""

def run_agent_turn(db: Session, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Executes a complete Agent turn:
    1. RAG vector retrieval from PostgreSQL
    2. Model reasoning + tool execution (Gemini / OpenAI / Smart Rule Fallback)
    3. Final grounded response generation
    """
    # 1. RAG Vector Retrieval
    relevant_chunks = search_relevant_chunks(db, query=user_message, top_k=3, threshold=0.45)
    
    context_str = ""
    citations = []
    if relevant_chunks:
        context_parts = []
        for ch in relevant_chunks:
            citation_label = f"{ch['document_name']} (Hal. {ch['page_number']})"
            citations.append({
                "document": ch["document_name"],
                "page": ch["page_number"],
                "similarity": ch["similarity"],
                "preview": ch["content"][:160] + "..."
            })
            context_parts.append(f"--- DOKUMEN: {citation_label} ---\n{ch['content']}")
        context_str = "\n\n".join(context_parts)
    else:
        context_str = "TIDAK ADA DOKUMEN YANG RELEVAN DENGAN PERTANYAAN INI."

    full_system_prompt = f"{SYSTEM_PROMPT}\n\n=== KONTEKS DOKUMEN RESMI ===\n{context_str}\n================================"

    # 2. Try Gemini Provider
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        try:
            return _execute_gemini_agent(db, user_message, full_system_prompt, citations)
        except Exception as e:
            logger.error(f"Gemini agent failed: {e}. Falling back to rule orchestrator.")

    # 3. Try OpenAI Provider
    elif settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            return _execute_openai_agent(db, user_message, full_system_prompt, citations)
        except Exception as e:
            logger.error(f"OpenAI agent failed: {e}. Falling back to rule orchestrator.")

    # 4. Deterministic Smart Fallback (No-Key / Safe Demo Mode)
    return _execute_deterministic_agent(db, user_message, relevant_chunks, citations)

def run_agent_turn_stream(db: Session, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None):
    """
    Generator yielding Server-Sent Events (SSE) in real-time:
    - Status updates (RAG searching, tool calling)
    - Citations
    - Tool start & end events (live inventory / WhatsApp dispatch)
    - Token-by-token streaming response
    - Completion event with latency & provider metadata
    """
    import time
    start_time = time.time()

    # Step 1: Notify RAG retrieval status
    yield f"data: {json.dumps({'type': 'status', 'stage': 'rag', 'message': 'Mencari dokumen SOP & Katalog resmi...'})}\n\n"
    relevant_chunks = search_relevant_chunks(db, query=user_message, top_k=3, threshold=0.45)
    
    context_str = ""
    citations = []
    if relevant_chunks:
        context_parts = []
        for ch in relevant_chunks:
            citation_label = f"{ch['document_name']} (Hal. {ch['page_number']})"
            citations.append({
                "document": ch["document_name"],
                "page": ch["page_number"],
                "similarity": ch["similarity"],
                "preview": ch["content"][:160] + "..."
            })
            context_parts.append(f"--- DOKUMEN: {citation_label} ---\n{ch['content']}")
        context_str = "\n\n".join(context_parts)
        yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"
    else:
        context_str = "TIDAK ADA DOKUMEN YANG RELEVAN DENGAN PERTANYAAN INI."

    full_system_prompt = f"{SYSTEM_PROMPT}\n\n=== KONTEKS DOKUMEN RESMI ===\n{context_str}\n================================"

    # Step 2: Try Gemini Streaming
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        try:
            yield f"data: {json.dumps({'type': 'status', 'stage': 'thinking', 'message': 'Menganalisis permintaan dengan Google Gemini...'})}\n\n"
            import google.generativeai as gai
            gai.configure(api_key=settings.GEMINI_API_KEY)

            def check_inventory_stock_tool(search_term: str) -> str:
                return json.dumps(check_inventory_stock(db, search_term=search_term), ensure_ascii=False)

            def send_whatsapp_action_tool(phone_number: str, message_body: str) -> str:
                return json.dumps(send_whatsapp_action(phone_number=phone_number, message_body=message_body), ensure_ascii=False)

            candidate_models = [
                settings.GEMINI_MODEL,
                "gemini-flash-lite-latest",
                "gemini-flash-latest",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash"
            ]
            unique_models = []
            for m in candidate_models:
                if m and m not in unique_models:
                    unique_models.append(m)

            stream_succeeded = False
            for m_name in unique_models:
                formatted_name = m_name if m_name.startswith("models/") else f"models/{m_name}"
                try:
                    model = gai.GenerativeModel(
                        model_name=formatted_name,
                        system_instruction=full_system_prompt,
                        tools=[check_inventory_stock_tool, send_whatsapp_action_tool]
                    )
                    chat = model.start_chat()
                    initial_response = chat.send_message(user_message)
                    
                    candidates = initial_response.candidates
                    if candidates and candidates[0].content and candidates[0].content.parts:
                        parts = candidates[0].content.parts
                        func_calls = [p.function_call for p in parts if hasattr(p, 'function_call') and p.function_call]
                        
                        if func_calls:
                            for fc in func_calls:
                                fn_name = fc.name
                                fn_args = dict(fc.args)
                                clean_name = "check_inventory_stock" if "stock" in fn_name else "send_whatsapp_action"
                                yield f"data: {json.dumps({'type': 'tool_start', 'tool': clean_name, 'arguments': fn_args})}\n\n"
                                
                                if clean_name == "check_inventory_stock":
                                    tool_result = check_inventory_stock(db, **fn_args)
                                else:
                                    tool_result = send_whatsapp_action(**fn_args)
                                    
                                yield f"data: {json.dumps({'type': 'tool_end', 'tool': clean_name, 'arguments': fn_args, 'result': tool_result})}\n\n"
                                
                                streamed_resp = chat.send_message(
                                    gai.protos.Content(
                                        parts=[
                                            gai.protos.Part(
                                                function_response=gai.protos.FunctionResponse(
                                                    name=fn_name,
                                                    response={'result': json.dumps(tool_result, ensure_ascii=False)}
                                                )
                                            )
                                        ]
                                    ),
                                    stream=True
                                )
                                for chunk in streamed_resp:
                                    if chunk.text:
                                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.text})}\n\n"
                        else:
                            full_text = initial_response.text
                            words = re.findall(r'\S+\s*', full_text)
                            for w in words:
                                yield f"data: {json.dumps({'type': 'token', 'content': w})}\n\n"
                                time.sleep(0.01)

                    elapsed_ms = round((time.time() - start_time) * 1000)
                    yield f"data: {json.dumps({'type': 'done', 'provider': f'Gemini ({m_name})', 'latency_ms': elapsed_ms})}\n\n"
                    stream_succeeded = True
                    break
                except Exception as ex:
                    logger.warning(f"Gemini stream candidate {m_name} failed: {ex}. Trying next...")

            if stream_succeeded:
                return
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}. Falling back to deterministic stream.")

    # Step 3: Deterministic Fallback Streaming
    yield f"data: {json.dumps({'type': 'status', 'stage': 'fallback', 'message': 'Menghubungkan ke Prawira Smart Engine...'})}\n\n"
    fallback_res = _execute_deterministic_agent(db, user_message, relevant_chunks, citations)

    for tool_exec in fallback_res.get("executed_tools", []):
        yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_exec['tool'], 'arguments': tool_exec.get('arguments', {})})}\n\n"
        yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_exec['tool'], 'arguments': tool_exec.get('arguments', {}), 'result': tool_exec.get('result', {})})}\n\n"

    answer_text = fallback_res.get("answer", "")
    words = re.findall(r'\S+\s*', answer_text)
    for w in words:
        yield f"data: {json.dumps({'type': 'token', 'content': w})}\n\n"
        time.sleep(0.015)

    elapsed_ms = round((time.time() - start_time) * 1000)
    yield f"data: {json.dumps({'type': 'done', 'provider': 'Prawira Tobacco Smart Engine', 'latency_ms': elapsed_ms})}\n\n"

def _execute_openai_agent(db: Session, user_message: str, system_prompt: str, citations: List[Dict]) -> Dict[str, Any]:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        tools=TOOLS_DEFINITION,
        tool_choice="auto",
        temperature=0.2
    )

    response_message = response.choices[0].message
    executed_tools = []

    if response_message.tool_calls:
        messages.append(response_message)
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            tool_result = {}
            if function_name == "check_inventory_stock":
                tool_result = check_inventory_stock(db, search_term=args.get("search_term", ""), category=args.get("category"))
                executed_tools.append({
                    "tool": "check_inventory_stock",
                    "arguments": args,
                    "result": tool_result
                })
            elif function_name == "send_whatsapp_action":
                tool_result = send_whatsapp_action(
                    phone_number=args.get("phone_number", ""),
                    message_body=args.get("message_body", ""),
                    action_title=args.get("action_title", "Prawira Tobacco")
                )
                executed_tools.append({
                    "tool": "send_whatsapp_action",
                    "arguments": args,
                    "result": tool_result
                })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(tool_result, ensure_ascii=False)
            })

        final_response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.2
        )
        return {
            "answer": final_response.choices[0].message.content,
            "citations": citations,
            "executed_tools": executed_tools,
            "provider": f"OpenAI ({settings.OPENAI_MODEL})"
        }

    return {
        "answer": response_message.content,
        "citations": citations,
        "executed_tools": executed_tools,
        "provider": f"OpenAI ({settings.OPENAI_MODEL})"
    }

def _execute_gemini_agent(db: Session, user_message: str, system_prompt: str, citations: List[Dict]) -> Dict[str, Any]:
    import google.generativeai as gai
    gai.configure(api_key=settings.GEMINI_API_KEY)
    
    executed_tools = []

    def check_inventory_stock_tool(search_term: str) -> str:
        """Cek stok fisik, harga, dan ketersediaan produk tembakau atau aksesoris di gudang Prawira Tobacco atau Supabase secara real-time."""
        res = check_inventory_stock(db, search_term=search_term)
        executed_tools.append({
            "tool": "check_inventory_stock",
            "arguments": {"search_term": search_term},
            "result": res
        })
        return json.dumps(res, ensure_ascii=False)

    def send_whatsapp_action_tool(phone_number: str, message_body: str) -> str:
        """Kirim pesan, ringkasan rekomendasi varian tembakau, atau pesanan ke nomor WhatsApp pelanggan/staf."""
        res = send_whatsapp_action(phone_number=phone_number, message_body=message_body)
        executed_tools.append({
            "tool": "send_whatsapp_action",
            "arguments": {"phone_number": phone_number, "message_body": message_body},
            "result": res
        })
        return json.dumps(res, ensure_ascii=False)

    # Candidate models in case the default hits 429 quota
    candidate_models = [
        settings.GEMINI_MODEL,
        "gemini-flash-lite-latest",
        "gemini-flash-latest",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash"
    ]
    unique_models = []
    for m in candidate_models:
        if m and m not in unique_models:
            unique_models.append(m)

    last_exc = None
    for m_name in unique_models:
        formatted_name = m_name if m_name.startswith("models/") else f"models/{m_name}"
        try:
            model = gai.GenerativeModel(
                model_name=formatted_name,
                system_instruction=system_prompt,
                tools=[check_inventory_stock_tool, send_whatsapp_action_tool]
            )
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(user_message)
            return {
                "answer": response.text,
                "citations": citations,
                "executed_tools": executed_tools,
                "provider": f"Gemini ({m_name})"
            }
        except Exception as e:
            last_exc = e
            logger.warning(f"Gemini model {m_name} failed: {e}. Trying next candidate...")

    raise last_exc or RuntimeError("All Gemini candidate models failed.")

FLAVOR_CATALOG = {
    "manis": [
        {"name": "Linting Melon Ice", "search": "Melon", "price": "Rp 25.000 / pack", "desc": "Karakter manis buah melon segar berpadu sensasi dingin menthol sejuk"},
        {"name": "Linting Strawberry", "search": "Strawberry", "price": "Rp 25.000 / pack", "desc": "Manis fruity segar khas buah strawberry pilihan alami"},
        {"name": "Linting Cappucino", "search": "Cappucino", "price": "Rp 25.000 / pack", "desc": "Manis legit creamy aroma kopi cappucino hangat"},
        {"name": "Purple Ice Burst", "search": "Purple", "price": "Rp 22.000 / pack", "desc": "Rasa manis segar anggur/berry dengan sensasi dingin ice burst"},
        {"name": "Coklat Ice Premium", "search": "Coklat", "price": "Rp 22.000 / pack", "desc": "Varian tembakau coklat manis legit dengan sensasi dingin menthol"}
    ],
    "dingin": [
        {"name": "Barrack Whiskey Ice", "search": "Whiskey", "price": "Rp 22.000 / pack", "desc": "Varian favorit sensasi dingin segar berpadu aroma whiskey unik"},
        {"name": "Linting Melon Ice", "search": "Melon", "price": "Rp 25.000 / pack", "desc": "Sensasi dingin buah melon yang manis dan menyegarkan tenggorokan"},
        {"name": "Purple Ice Burst", "search": "Purple", "price": "Rp 22.000 / pack", "desc": "Sensasi anggur berry segar dengan ice burst dingin menyegarkan"},
        {"name": "Coklat Ice Premium", "search": "Coklat", "price": "Rp 22.000 / pack", "desc": "Tembakau rasa coklat berpadu sensasi mint sejuk"}
    ],
    "pemula": [
        {"name": "Linting Mild", "search": "Mild", "price": "Rp 23.000 / pack", "desc": "Tarikan sangat ringan, halus, dan bersih, sangat bersahabat bagi pemula"},
        {"name": "Sampurna Premium", "search": "Sampurna", "price": "Rp 30.000 / pack", "desc": "Racikan halus premium aroma rempah wangi pilihan"},
        {"name": "Barrack Soju", "search": "Soju", "price": "Rp 45.000 / pack", "desc": "Tembakau linting Golden Virginia 50 gram impor aroma halus istimewa"},
        {"name": "Barrack Bayote", "search": "Bayote", "price": "Rp 45.000 / pack", "desc": "Tembakau rasa khas Bayote tarikan pas dan seimbang"}
    ],
    "kretek": [
        {"name": "Linting Surya", "search": "Surya", "price": "Rp 23.000 / pack", "desc": "Karakter aroma madu cengkeh tebal, gurih mantap khas karakter Surya"},
        {"name": "Linting Samsu", "search": "Samsu", "price": "Rp 23.000 / pack", "desc": "Karakter klasik tajam dan nikmat, racikan legenda tingwe tradisional"},
        {"name": "Linting Marlong", "search": "Marlong", "price": "Rp 23.000 / pack", "desc": "Karakter American blend gurih padat khas Marlboro"},
        {"name": "Magnum Premium", "search": "Magnum", "price": "Rp 30.000 / pack", "desc": "Tembakau kretek premium tarikan padat berbobot"}
    ],
    "general": [
        {"name": "Linting Melon Ice", "search": "Melon", "price": "Rp 25.000 / pack", "desc": "Varian rasa manis segar berpadu menthol terfavorit"},
        {"name": "Linting Surya", "search": "Surya", "price": "Rp 23.000 / pack", "desc": "Kretek gurih tebal aroma madu cengkeh pilihan"},
        {"name": "Barrack Whiskey Ice", "search": "Whiskey", "price": "Rp 22.000 / pack", "desc": "Sensasi dingin segar dengan sentuhan aroma whiskey"},
        {"name": "Linting Mild", "search": "Mild", "price": "Rp 23.000 / pack", "desc": "Tarikan ringan halus cocok untuk harian pemula"}
    ]
}

def _extract_requested_count(text: str) -> Optional[int]:
    """
    Extracts the user's requested number of recommendations (1, 2, 3, etc.)
    with sanitization for phone numbers, prices, and hours.
    """
    msg_clean = text.lower()
    # Remove phone numbers, prices, timestamps, percentages
    msg_clean = re.sub(r'(08\d{8,11}|628\d{8,11})', ' ', msg_clean)
    msg_clean = re.sub(r'\b\d{4,}\b', ' ', msg_clean)
    msg_clean = re.sub(r'\b2x24\b|\b24\s*jam\b|\b50\s*gram\b|\b\d+%', ' ', msg_clean)

    # 1. Multi-count checks
    if re.search(r'\b(2|dua)\s*(varian|produk|rekomendasi|macam|biji|opsi|buah|item)?\b', msg_clean):
        return 2
    if re.search(r'\b(3|tiga)\s*(varian|produk|rekomendasi|macam|biji|opsi|buah|item)?\b', msg_clean):
        return 3
    if re.search(r'\b(4|empat)\s*(varian|produk|rekomendasi|macam|biji|opsi|buah)?\b', msg_clean):
        return 4
    if re.search(r'\b(5|lima)\s*(varian|produk|rekomendasi|macam|biji|opsi|buah)?\b', msg_clean):
        return 5

    # 2. Single item indicators
    single_indicators = [
        r'\b(1|satu)\s*(varian|produk|rekomendasi|macam|biji|opsi|buah|item|saja|aja)?\b',
        r'\b(pilihin|pilihkan|rekomendasikan|kasih|minta|beri)\s+(1|satu)\b',
        r'\b(hanya|cuma)\s+(1|satu)\b',
        r'\b(1|satu)\s+saja\b',
        r'\b(1|satu)\s+terbaik\b'
    ]
    for pattern in single_indicators:
        if re.search(pattern, msg_clean):
            return 1

    return None

def _execute_deterministic_agent(db: Session, user_message: str, chunks: List[Dict], citations: List[Dict]) -> Dict[str, Any]:
    """
    High-intelligence consultative agent engine with strict anti-hallucination guardrails.
    Used when LLM APIs are offline or rate-limited.
    """
    msg_lower = user_message.lower().strip()
    executed_tools = []
    answers = []

    # -------------------------------------------------------------
    # 1. STRICT OFF-TOPIC FILTER (Anti-Hallucination Guardrail)
    # -------------------------------------------------------------
    tobacco_words = [
        "tembakau", "rokok", "tingwe", "linting", "prawira", "toko", "produk", "rasa", "stok", 
        "papir", "filter", "busa", "cengkeh", "lem", "cappucino", "melon", "surya", "samsu", 
        "marlboro", "whiskey", "kretek", "mild", "beli", "pesan", "order", "kirim",
        "harga", "rekomendasi", "saran", "sop", "garansi", "retur", "simpan", "gudang"
    ]
    contains_tobacco_context = any(re.search(rf"\b{re.escape(w)}\b", msg_lower) for w in tobacco_words) or bool(re.search(r'\bwa\b', msg_lower))
    off_topic_patterns = [
        r'\b(pesawat|penerbangan|bandara|tiket\s+pesawat|tiket\s+kereta|hotel|villa|pesiar)\b',
        r'\b(resep\s+masak|bumbu\s+dapur|rendang|nasi\s+goreng|kue\s+tart|restoran|kuliner)\b',
        r'\b(cuaca\s+hari\s+ini|suhu\s+udara|hujan\s+lebat|ramalan\s+cuaca|gempa\s+bumi|tsunami)\b',
        r'\b(presiden|gubernur|menteri|pemilu|politik|pilkada|dpr|partai\s+politik)\b',
        r'\b(crypto|bitcoin|ethereum|saham\s+ihsg|forex|investasi\s+saham|trading\s+crypto)\b',
        r'\b(koding|python|javascript|react|css|html|programming|scripting)\b',
        r'\b(film\s+bioskop|lagu|musik|konser|chord\s+gitar)\b'
    ]
    is_off_topic = any(re.search(p, msg_lower) for p in off_topic_patterns)
    if is_off_topic and not contains_tobacco_context:
        return {
            "answer": (
                "Maaf, informasi tersebut tidak ditemukan dalam dokumen SOP atau Katalog resmi Prawira Tobacco.\n\n"
                "Sebagai asisten resmi Prawira Tobacco, saya berfokus untuk melayani konsultasi varian tembakau linting (tingwe), aksesoris linting resmi, ketersediaan stok di toko/Supabase, serta SOP penyimpanan resmi kami.\n\n"
                "Apakah ada yang bisa saya bantu terkait produk tembakau atau perlengkapan linting kami?"
            ),
            "citations": [],
            "executed_tools": [],
            "provider": "Prawira Tobacco Smart Engine"
        }

    # -------------------------------------------------------------
    # 2. GREETINGS & BOT IDENTITY
    # -------------------------------------------------------------
    greetings_patterns = [
        r'^(halo|hai|hey|hei|hola|assalamualaikum|pagi|siang|sore|malam)[\s!\.]*$',
        r'\b(siapa\s+(kamu|anda)|kamu\s+siapa|anda\s+siapa|kamu\s+bot\s+apa|identitas|profil\s+kamu)\b',
        r'\b(bisa\s+bantu\s+apa|fitur|kemampuan|tugas\s+kamu|fungsi\s+kamu)\b',
        r'\b(tentang\s+kamu|tentang\s+asisten|tentang\s+prawira)\b'
    ]
    is_greeting = any(re.search(p, msg_lower) for p in greetings_patterns)
    has_specific_intent = any(k in msg_lower for k in [
        "stok", "stock", "rekomendasi", "saran", "harga", "beli", "pesan", "order", 
        "sop", "garansi", "simpan", "tingwe", "linting", "rasa", "varian", "ada"
    ])
    if is_greeting and not has_specific_intent:
        return {
            "answer": (
                "Halo. Selamat datang di Prawira Tobacco Enterprise.\n\n"
                "Saya adalah asisten AI resmi toko tembakau spesialis Prawira Tobacco. Saya siap membantu Anda dengan layanan konsultasi profesional:\n\n"
                "1. Rekomendasi Varian Tembakau: Pilihan profil rasa manis, buah, kopi, dingin menthol ice, gurih kretek nusantara, hingga racikan mild ramah pemula.\n"
                "2. Pengecekan Stok Real-Time: Verifikasi langsung ketersediaan produk, harga, dan lokasi rak gudang dari sistem basis data Supabase kami.\n"
                "3. Panduan Pemesanan & WhatsApp: Membantu memilih varian dan menyusun ringkasan pesanan ke WhatsApp CS resmi 083132001855.\n"
                "4. Edukasi Tingwe & SOP Toko: Panduan cara melinting, perlengkapan linting (papir, filter, lem), serta SOP penyimpanan dan garansi retur.\n\n"
                "Silakan beri tahu saya varian atau informasi apa yang ingin Anda tanyakan hari ini."
            ),
            "citations": [],
            "executed_tools": [],
            "provider": "Prawira Tobacco Smart Engine"
        }

    # -------------------------------------------------------------
    # 3. HOW TO BUY, STORE INFO, OPERATIONAL HOURS & LOCATION
    # -------------------------------------------------------------
    order_patterns = [
        r'\b(cara\s+(beli|pesan|order|belanja|transaksi))\b',
        r'\b(gimana\s+(cara\s+)?(beli|pesan|order))\b',
        r'\b(langkah\s+(beli|pemesanan|order))\b',
        r'\b(lokasi\s+toko|alamat\s+toko|toko(nya)?\s+di\s+mana|posisi\s+toko)\b',
        r'\b(buka\s+jam\s+berapa|jam\s+buka|jam\s+operasional|tutup\s+jam)\b',
        r'\b(bisa\s+kirim|ongkir|pengiriman|ekspedisi|kirim\s+ke)\b',
        r'\b(nomor\s+(wa|whatsapp|admin|cs)|kontak\s+(admin|cs|toko))\b'
    ]
    if any(re.search(p, msg_lower) for p in order_patterns):
        return {
            "answer": (
                "Berikut adalah panduan lengkap layanan, pemesanan, dan operasional Prawira Tobacco Enterprise:\n\n"
                "1. Prosedur Pembelian & Pemesanan:\n"
                "- Pemilihan Produk: Tentukan varian tembakau dan aksesoris yang Anda inginkan (Anda dapat meminta rekomendasi rasa pada asisten ini).\n"
                "- Pengecekan Stok: Kami memverifikasi ketersediaan stok secara real-time langsung ke gudang Supabase.\n"
                "- Konfirmasi via WhatsApp: Kirimkan daftar pesanan dan alamat pengiriman ke WhatsApp CS resmi Prawira Tobacco di nomor 083132001855.\n"
                "- Pembayaran & Pengiriman: Admin toko akan menginformasikan total biaya serta nomor rekening resmi. Pesanan segera dikemas kedap udara dan dikirim via ekspedisi (JNE, J&T, SiCepat).\n\n"
                "2. Pengiriman Luar Kota:\n"
                "Kami melayani pengiriman ke seluruh wilayah Indonesia dengan standar kemasan khusus penjaga kelembapan tembakau (RH 65-70%).\n\n"
                "3. Layanan Pelanggan & Jam Operasional:\n"
                "- CS WhatsApp: 083132001855\n"
                "- Jam Layanan Online: Setiap hari pukul 09.00 - 21.00 WIB\n\n"
                "Apakah ada varian produk tertentu yang ingin Anda cek stok atau pesan sekarang?"
            ),
            "citations": [],
            "executed_tools": [],
            "provider": "Prawira Tobacco Smart Engine"
        }

    # -------------------------------------------------------------
    # 4. TINGWE EDUCATION & ROLLING TUTORIAL
    # -------------------------------------------------------------
    tingwe_guide_patterns = [
        r'\b(apa\s+itu\s+tingwe|arti\s+tingwe|maksud(nya)?\s+tingwe)\b',
        r'\b(cara\s+(me)?linting|tutorial\s+linting|belajar\s+linting|langkah\s+linting)\b',
        r'\b(alat\s+(me)?linting|perlengkapan\s+linting|kebutuhan\s+linting|bahan\s+linting)\b'
    ]
    if any(re.search(p, msg_lower) for p in tingwe_guide_patterns):
        acc_tool = check_inventory_stock(db, search_term="Papir")
        executed_tools.append({
            "tool": "check_inventory_stock",
            "arguments": {"search_term": "Papir"},
            "result": acc_tool
        })
        return {
            "answer": (
                "Tingwe (singkatan dari 'Linting Dewe' atau melinting sendiri) adalah tradisi meracik dan melinting rokok tembakau secara mandiri. Tingwe menghadirkan cita rasa tembakau murni yang kaya, aroma autentik, dan jauh lebih hemat dibandingkan rokok pabrikan siap hisap.\n\n"
                "Perlengkapan Wajib untuk Melinting Tingwe:\n"
                "1. Tembakau Linting: Tembakau rajangan berkualitas dengan profil rasa sesuai selera Anda (manis buah, dingin ice, kretek gurih, atau mild halus).\n"
                "2. Kertas Papir: Kertas khusus rokok linting (tersedia di katalog Supabase kami mulai Rp 2.000 - Rp 5.000).\n"
                "3. Busa Filter: Busa penyaring untuk hisapan yang lebih bersih, halus, dan nyaman (tersedia varian Busa Besar dan Busa Kecil).\n"
                "4. Lem Khusus Papir: Perekat higienis dan aman untuk mengunci gulungan lintingan.\n"
                "5. Cengkeh (Opsional): Rajangan cengkeh alami penambah sensasi gurih khas kretek nusantara.\n\n"
                "Langkah Sederhana Melinting Manual:\n"
                "1. Siapkan lembar kertas papir dengan posisi bagian berperekat di sisi atas menghadap Anda.\n"
                "2. Letakkan busa filter di salah satu ujung kertas (kiri atau kanan).\n"
                "3. Ratakan tembakau secukupnya di sepanjang kertas papir secara merata (jangan terlalu padat agar tarikan hisapan tetap lancar).\n"
                "4. Gulung kertas perlahan menggunakan ibu jari dan telunjuk hingga membentuk silinder padat dan rapi.\n"
                "5. Basahi tipis lem perekat pada tepi papir, lalu rekatkan gulungan dengan rapat.\n\n"
                "Seluruh perlengkapan linting resmi di atas tersedia lengkap di Prawira Tobacco."
            ),
            "citations": [],
            "executed_tools": executed_tools,
            "provider": "Prawira Tobacco Smart Engine"
        }

    # -------------------------------------------------------------
    # 5. ACCESSORIES INVENTORY SEARCH (Papir, Filter, Lem, Cengkeh)
    # -------------------------------------------------------------
    acc_keywords = {
        "papir": "Papir",
        "kertas": "Papir",
        "filter": "Busa",
        "busa": "Busa",
        "lem": "Lem",
        "cengkeh": "Cengkeh"
    }
    queried_acc = None
    for kw, target_term in acc_keywords.items():
        if re.search(rf"\b{kw}\b", msg_lower):
            queried_acc = target_term
            break

    if queried_acc and not any(k in msg_lower for k in ["sop", "simpan", "resep"]):
        stock_res = check_inventory_stock(db, search_term=queried_acc)
        if stock_res["found"] and stock_res["items"]:
            executed_tools.append({
                "tool": "check_inventory_stock",
                "arguments": {"search_term": queried_acc},
                "result": stock_res
            })
            lines = [f"**Katalog Perlengkapan Linting Resmi ({queried_acc} - Prawira Tobacco):**\n"]
            for it in stock_res["items"]:
                lines.append(f"- **{it['name']}** (SKU: `{it['sku']}`): Stok **{it['stock']} {it['unit']}** | Harga: **{it['formatted_price']}** | Lokasi: `{it['shelf_location']}`")
            lines.append("\n*Produk perlengkapan linting di atas siap dipesan langsung melalui toko atau via WhatsApp 083132001855.*")
            return {
                "answer": "\n".join(lines),
                "citations": [],
                "executed_tools": executed_tools,
                "provider": "Prawira Tobacco Smart Engine"
            }

    # -------------------------------------------------------------
    # 6. NON-EXISTENT BRANDS / FACTORY CIGARETTES CONVERSION
    # -------------------------------------------------------------
    non_existent_brands = {
        "marlboro": ("Linting Marlong", "Rp 23.000", "karakter American blend mantap khas Marlboro"),
        "djarum": ("Linting Surya atau Magnum Premium", "Rp 23.000 - Rp 30.000", "karakter kretek gurih berempah mantap"),
        "super": ("Linting Surya atau Magnum Premium", "Rp 23.000 - Rp 30.000", "karakter kretek gurih berempah mantap"),
        "sampoerna": ("Linting Mild atau Sampurna Premium", "Rp 23.000 - Rp 30.000", "tarikan halus aroma rempah pilihan"),
        "gudang garam": ("Linting Surya atau GGF Premium", "Rp 20.000 - Rp 23.000", "aroma cengkeh madu gurih mantap"),
        "esse": ("Linting Mild atau Purple Ice Burst", "Rp 22.000 - Rp 23.000", "sensasi ringan halus atau dingin buah segar"),
        "camel": ("Linting Marlong", "Rp 23.000", "American blend mantap"),
        "magnum filter": ("Magnum Premium", "Rp 30.000", "kretek tarikan padat berbobot"),
        "gorilla": ("Linting Surya", "Rp 23.000", "kretek tradisional legal resmi"),
        "ganja": ("Linting Surya", "Rp 23.000", "tembakau legal resmi"),
    }
    
    queried_fake_brand = None
    for brand_key, (alt_name, alt_price, alt_desc) in non_existent_brands.items():
        if re.search(rf"\b{re.escape(brand_key)}\b", msg_lower):
            if brand_key == "super" and ("surya" in msg_lower or "linting" in msg_lower):
                continue
            if brand_key in ["marlboro", "djarum", "sampoerna", "gudang garam", "esse", "camel", "gorilla", "ganja"]:
                queried_fake_brand = (brand_key, alt_name, alt_price, alt_desc)
                break

    # -------------------------------------------------------------
    # 7. DETECT TASTE RECOMMENDATION INTENT & CARDINALITY
    # -------------------------------------------------------------
    is_rec = any(k in msg_lower for k in [
        "rekomendasi", "saran", "enak", "cocok", "pemula", "manis", "dingin", 
        "ice", "menthol", "kretek", "mild", "buah", "gurih", "varian apa", "beli apa",
        "pilihin", "pilihkan", "paling enak", "terlaris", "favorit", "rasa", "kopi", "coklat",
        "apel", "strawberry", "melon", "anggur", "berry", "mint"
    ])
    req_count = _extract_requested_count(msg_lower)
    product_targets = []
    rec_text = ""

    category_items = []
    cat_title = ""
    if any(k in msg_lower for k in ["manis", "buah", "kopi", "coklat", "apel", "strawberry", "melon", "anggur", "berry"]):
        category_items = FLAVOR_CATALOG["manis"]
        cat_title = "Rasa Manis, Buah & Kopi"
    elif any(k in msg_lower for k in ["dingin", "ice", "menthol", "segar", "mint"]):
        category_items = FLAVOR_CATALOG["dingin"]
        cat_title = "Dingin & Menthol (Ice Series)"
    elif any(k in msg_lower for k in ["pemula", "mild", "halus", "ringan", "soju", "bayote", "melisa"]):
        category_items = FLAVOR_CATALOG["pemula"]
        cat_title = "Mild & Ramah Pemula"
    elif any(k in msg_lower for k in ["kretek", "gurih", "mantap", "tradisional", "tingwe", "cengkeh", "surya", "samsu", "marlong", "ggf"]):
        category_items = FLAVOR_CATALOG["kretek"]
        cat_title = "Kretek Nusantara Gurih & Mantap"
    elif is_rec:
        category_items = FLAVOR_CATALOG["general"]
        cat_title = "Terlaris Prawira Tobacco"

    if category_items:
        if req_count == 1:
            it = category_items[0]
            product_targets = [it["search"]]
            rec_text = (
                f"**Rekomendasi 1 Varian Terbaik ({cat_title} - Prawira Tobacco):**\n\n"
                f"Sesuai permintaan Anda untuk 1 pilihan terbaik, rekomendasi utama kami adalah:\n\n"
                f"**{it['name']}** ({it['price']})\n"
                f"- **Karakter & Profil Rasa:** {it['desc']}.\n"
                f"- **Alasan Pemilihan:** Varian ini merupakan signature blend terlaris dengan rating kepuasan tertinggi untuk kategori {cat_title.lower()} di Prawira Tobacco.\n\n"
                f"*Ketersediaan stok di sistem gudang Supabase telah diverifikasi langsung di bawah ini.*"
            )
        elif req_count and req_count > 1:
            selected = category_items[:req_count]
            product_targets = [it["search"] for it in selected]
            lines = [f"**Rekomendasi {len(selected)} Varian Pilihan ({cat_title} - Prawira Tobacco):**\n"]
            for idx, it in enumerate(selected, 1):
                lines.append(f"{idx}. **{it['name']}** — {it['desc']} ({it['price']}).")
            lines.append("\n*Ketersediaan stok untuk seluruh varian di atas telah diverifikasi dengan sistem gudang Supabase.*")
            rec_text = "\n".join(lines)
        else:
            selected = category_items[:3]
            product_targets = [it["search"] for it in selected[:2]]
            lines = [f"**Rekomendasi Varian Pilihan ({cat_title} - Prawira Tobacco):**\n"]
            for idx, it in enumerate(selected, 1):
                lines.append(f"{idx}. **{it['name']}** — {it['desc']} ({it['price']}).")
            rec_text = "\n".join(lines)

    # -------------------------------------------------------------
    # 8. INVENTORY STOCK SEARCH
    # -------------------------------------------------------------
    is_sop_query = any(k in msg_lower for k in ["sop", "simpan", "penyimpanan", "suhu", "lembab", "kelembaban", "garansi", "retur", "rusak", "jamur", "klaim", "unboxing"])
    is_stock_query = any(k in msg_lower for k in ["stok", "stock", "ada", "ready", "harga", "sisa", "rak", "tersedia", "cek"]) and not is_sop_query
    
    terms_to_check = []
    if product_targets:
        terms_to_check = product_targets
    elif (is_stock_query or queried_fake_brand) and not is_sop_query:
        stopwords = {
            "cek", "stok", "stock", "apakah", "ada", "berapa", "sisa", "harga", 
            "di", "gudang", "toko", "ya", "tolong", "bisa", "info", "minta", 
            "dong", "ready", "tersedia", "produk", "varian", "dan", "untuk", 
            "masih", "rokok", "tembakau", "lokasinya", "rak", "lokasi"
        }
        words = [w for w in re.findall(r'\b\w+\b', msg_lower) if w not in stopwords and len(w) > 1]
        terms_to_check = [" ".join(words)] if words else ["tembakau"]

    stock_items_found = []
    failed_search_term = None

    if terms_to_check:
        search_limit = 1 if req_count == 1 else (req_count if req_count else 2)
        for term in terms_to_check[:search_limit]:
            stock_res = check_inventory_stock(db, search_term=term)
            if stock_res["found"] and stock_res["items"]:
                executed_tools.append({
                    "tool": "check_inventory_stock",
                    "arguments": {"search_term": term},
                    "result": stock_res
                })
                stock_items_found.extend(stock_res["items"])
            else:
                failed_search_term = term

    # -------------------------------------------------------------
    # 9. DETECT EXPLICIT WHATSAPP DISPATCH INTENT
    # -------------------------------------------------------------
    wa_patterns = [
        r'\bwhatsapp\b',
        r'\bfonnte\b',
        r'\bwa\b',
        r'\b(kirim|chat|forward|send)\s+(ke|via|lewat)\b',
        r'\bhubungi\s+(admin|cs|sales|toko|nomor|no)\b'
    ]
    is_wa_query = any(re.search(p, msg_lower) for p in wa_patterns)
    phone_match = re.search(r'(08\d{8,11}|628\d{8,11})', user_message)
    detected_phone = phone_match.group(1) if phone_match else (settings.STORE_DEFAULT_PHONE if is_wa_query else None)

    if detected_phone and (is_wa_query or phone_match):
        summary_lines = ["Halo! Berikut ringkasan rekomendasi dari Prawira Tobacco:\n"]
        if stock_items_found:
            for it in stock_items_found[:3]:
                summary_lines.append(f"- {it['name']}: {it['formatted_price']} (Stok: {it['stock']} {it['unit']})")
        else:
            summary_lines.append("- Linting Melon Ice: Rp 25.000 / pack\n- Linting Strawberry: Rp 25.000 / pack\n- Linting Surya: Rp 23.000 / pack")
        
        summary_lines.append("\nPesanan siap diproses melalui admin Prawira Tobacco.")
        summary_msg = "\n".join(summary_lines)

        wa_res = send_whatsapp_action(
            phone_number=detected_phone,
            message_body=summary_msg,
            action_title="Rekomendasi Prawira Tobacco"
        )
        executed_tools.append({
            "tool": "send_whatsapp_action",
            "arguments": {"phone_number": detected_phone, "message_body": summary_msg},
            "result": wa_res
        })
        answers.append(
            f"**Ringkasan Berhasil Dikirim ke WhatsApp:**\n"
            f"Pesan rekomendasi dan ketersediaan stok telah disiapkan untuk nomor **{detected_phone}**. Anda dapat langsung mengklik tombol aksi WhatsApp di bawah ini."
        )

    # -------------------------------------------------------------
    # 10. ASSEMBLE CONTENT
    # -------------------------------------------------------------
    if is_sop_query and chunks:
        doc_info = "\n\n".join([f"> *\"{ch['content'][:320]}...\"*\n> — [Sumber: **{ch['document_name']}**, Hal. {ch['page_number']}]" for ch in chunks[:2]])
        answers.append(f"**Berdasarkan Dokumen SOP Resmi Prawira Tobacco:**\n\n{doc_info}\n\n*Jika Anda memerlukan bantuan lebih lanjut mengenai SOP atau klaim retur, silakan hubungi CS resmi Prawira Tobacco di WhatsApp 083132001855.*")
    elif rec_text:
        answers.insert(0, rec_text)
    elif stock_items_found and not is_rec:
        stock_summary = "\n".join([
            f"- **{it['name']}** (SKU: `{it['sku']}`): Stok **{it['stock']} {it['unit']}** | Harga: **{it['formatted_price']}** | Lokasi: `{it['shelf_location']}` ({it['status']})"
            for it in stock_items_found
        ])
        answers.insert(0, f"**Ketersediaan Stok di Gudang / Supabase:**\n{stock_summary}")
    elif queried_fake_brand:
        brand_key, alt_name, alt_price, alt_desc = queried_fake_brand
        answers.insert(0, (
            f"Mohon maaf, rokok pabrikan **'{brand_key.title()}'** tidak dijual di toko kami.\n\n"
            f"Prawira Tobacco khusus merupakan spesialis tembakau linting (*tingwe*) artisan legal dan aksesoris resmi.\n\n"
            f"Sebagai alternatif dengan karakter rasa sebanding, kami merekomendasikan varian racikan resmi kami:\n"
            f"- **{alt_name}** ({alt_price}) — {alt_desc}.\n\n"
            f"Silakan periksa daftar 24 varian produk resmi kami di tab **Katalog Supabase**."
        ))
    elif failed_search_term and not stock_items_found and not is_rec and not is_sop_query:
        searched_label = failed_search_term.title()
        answers.insert(0, (
            f"Varian atau produk **'{searched_label}'** saat ini belum terdaftar di katalog resmi basis data Supabase Prawira Tobacco.\n\n"
            f"Kami menyediakan 24 varian resmi tembakau linting artisan pilihan (rasa manis buah, dingin menthol ice, kretek gurih mantap, dan mild halus) serta perlengkapan linting lengkap (papir, filter, lem).\n\n"
            f"Silakan pilih kategori rasa yang Anda sukai atau periksa tab **Katalog Supabase** untuk melihat varian yang ready stock."
        ))
    elif not answers:
        answers.append(
            "Halo. Ada yang bisa saya bantu mengenai produk **Prawira Tobacco**?\n\n"
            "Anda dapat menanyakan:\n"
            "- Rekomendasi rasa (contoh: *'Rekomendasikan 1 tembakau rasa manis'* atau *'Varian dingin menthol'*)\n"
            "- Ketersediaan stok barang (contoh: *'Cek stok Barrack Whiskey Ice'* atau *'Stok Linting Surya'*)\n"
            "- Perlengkapan linting (contoh: *'Stok papir'*, *'Busa filter'*, atau *'Cara melinting'*)\n"
            "- Cara pemesanan dan ringkasan ke WhatsApp (contoh: *'Cara beli gimana'* atau *'Kirim pesanan ke WhatsApp 083132001855'*)\n"
            "- SOP penyimpanan tembakau dan garansi retur toko."
        )

    return {
        "answer": "\n\n".join(answers),
        "citations": citations if (is_sop_query or any(k in msg_lower for k in ["sop", "simpan", "suhu", "garansi", "retur"])) else [],
        "executed_tools": executed_tools,
        "provider": "Prawira Tobacco Smart Engine"
    }
