import os
from flask import Flask, request, send_file, render_template
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from PIL import Image, ImageDraw
import io
from werkzeug.utils import secure_filename
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

PAGE_WIDTH, PAGE_HEIGHT = A4
SIDEBAR_WIDTH = 6*cm
CONTENT_WIDTH = PAGE_WIDTH - SIDEBAR_WIDTH - 2*cm
MARGIN_TOP = PAGE_HEIGHT - 2*cm
MARGIN_BOTTOM = 2*cm
LINE_HEIGHT = 16

COLOR_PALETTES = {
    'professional': {
        'primary': colors.HexColor("#dc2626"),      # Professional red
        'secondary': colors.HexColor("#f59e0b"),    # Warm yellow accent
        'text': colors.HexColor("#374151"),         # Dark gray text
        'light_bg': colors.HexColor("#fef2f2"),     # Light pink background
        'white': colors.white,
        'border': colors.HexColor("#e5e7eb"),       # Light border
        'muted': colors.HexColor("#6b7280")         # Muted gray
    },
    'corporate': {
        'primary': colors.HexColor("#1e40af"),      # Corporate blue
        'secondary': colors.HexColor("#0891b2"),    # Cyan accent
        'text': colors.HexColor("#374151"),         # Dark gray text
        'light_bg': colors.HexColor("#eff6ff"),     # Light blue background
        'white': colors.white,
        'border': colors.HexColor("#e5e7eb"),       # Light border
        'muted': colors.HexColor("#6b7280")         # Muted gray
    },
    'modern': {
        'primary': colors.HexColor("#7c3aed"),      # Modern purple
        'secondary': colors.HexColor("#06b6d4"),    # Bright cyan
        'text': colors.HexColor("#374151"),         # Dark gray text
        'light_bg': colors.HexColor("#f3f4f6"),     # Light gray background
        'white': colors.white,
        'border': colors.HexColor("#e5e7eb"),       # Light border
        'muted': colors.HexColor("#6b7280")         # Muted gray
    },
    'elegant': {
        'primary': colors.HexColor("#059669"),      # Elegant green
        'secondary': colors.HexColor("#d97706"),    # Warm orange
        'text': colors.HexColor("#374151"),         # Dark gray text
        'light_bg': colors.HexColor("#f0fdf4"),     # Light green background
        'white': colors.white,
        'border': colors.HexColor("#e5e7eb"),       # Light border
        'muted': colors.HexColor("#6b7280")         # Muted gray
    }
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def create_circle_image(image_path):
    img = Image.open(image_path).convert("RGBA")
    size = (200, 200)  # Larger photo for better impact
    img = img.resize(size)
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0,0)+size, fill=255)
    img.putalpha(mask)
    
    output = Image.new('RGBA', size, (0, 0, 0, 0))
    output.paste(img, (0, 0), img)
    
    temp_path = os.path.join(UPLOAD_FOLDER, "temp_circle.png")
    output.save(temp_path)
    return temp_path

def draw_wrapped_text(pdf, text, x, y, max_width, font_name="Helvetica", font_size=11, line_height=16, color=None, colors_palette=None):
    COLORS = colors_palette or get_colors()
    if color is None:
        color = COLORS['text']
        
    paragraphs = text.split("\n")
    pdf.setFont(font_name, font_size)
    pdf.setFillColor(color)
    
    for para in paragraphs:
        if not para.strip():
            y -= line_height * 0.5
            continue
            
        words = para.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if stringWidth(test_line, font_name, font_size) > max_width:
                if line:
                    y -= line_height
                    if y < MARGIN_BOTTOM:
                        pdf.showPage()
                        draw_sidebar(pdf, foto_path=None, data=None, colors_palette=COLORS)
                        y = MARGIN_TOP
                        pdf.setFont(font_name, font_size)
                        pdf.setFillColor(color)
                    pdf.drawString(x, y, line)
                line = word
            else:
                line = test_line
        
        if line:
            y -= line_height
            if y < MARGIN_BOTTOM:
                pdf.showPage()
                draw_sidebar(pdf, foto_path=None, data=None, colors_palette=COLORS)
                y = MARGIN_TOP
                pdf.setFont(font_name, font_size)
                pdf.setFillColor(color)
            pdf.drawString(x, y, line)
    
    return y

def draw_wrapped_text_sidebar(pdf, text, x, y, max_width, font_name="Helvetica", font_size=10, line_height=14, colors_palette=None):
    COLORS = colors_palette or get_colors()
    
    pdf.setFont(font_name, font_size)
    pdf.setFillColor(COLORS['white'])
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if stringWidth(test_line, font_name, font_size) > max_width:
            if line:
                y -= line_height
                pdf.drawString(x, y, line)
            line = word
        else:
            line = test_line
    if line:
        y -= line_height
        pdf.drawString(x, y, line)
    return y

def draw_sidebar(pdf, foto_path=None, data=None, colors_palette=None):
    COLORS = colors_palette or get_colors()
    
    # Main sidebar background
    pdf.setFillColor(COLORS['text'])
    pdf.rect(0, 0, SIDEBAR_WIDTH, PAGE_HEIGHT, fill=1)
    
    # Red accent stripe
    pdf.setFillColor(COLORS['primary'])
    pdf.rect(0, 0, 0.4*cm, PAGE_HEIGHT, fill=1)
    
    y = PAGE_HEIGHT - 1.5*cm

    # Photo section with elegant frame
    if foto_path:
        # Red border around photo only
        pdf.setStrokeColor(COLORS['primary'])
        pdf.setLineWidth(3)
        pdf.circle(SIDEBAR_WIDTH/2, y-2.8*cm, 2.0*cm, fill=0)
        
        pdf.drawImage(foto_path, SIDEBAR_WIDTH/2-1.8*cm, y-4.6*cm, width=3.6*cm, height=3.6*cm, mask='auto')
        y -= 6*cm
    else:
        y -= 1*cm

    if data and data.get('nome'):
        pdf.setFillColor(COLORS['white'])
        
        # Start with larger font and reduce if needed
        font_size = 18
        max_width = SIDEBAR_WIDTH - 1*cm
        
        # Check if name fits in one line
        name_width = stringWidth(data['nome'], "Helvetica-Bold", font_size)
        
        if name_width <= max_width:
            # Name fits in one line - center it
            pdf.setFont("Helvetica-Bold", font_size)
            pdf.drawString((SIDEBAR_WIDTH - name_width)/2, y, data['nome'])
            y -= 2*cm
        else:
            # Name is too long - try smaller font first
            while name_width > max_width and font_size > 12:
                font_size -= 1
                name_width = stringWidth(data['nome'], "Helvetica-Bold", font_size)
            
            if name_width <= max_width:
                # Smaller font works - center it
                pdf.setFont("Helvetica-Bold", font_size)
                pdf.drawString((SIDEBAR_WIDTH - name_width)/2, y, data['nome'])
                y -= 2*cm
            else:
                # Even small font doesn't work - split into lines intelligently
                pdf.setFont("Helvetica-Bold", 14)  # Use readable font size
                words = data['nome'].split()
                
                if len(words) <= 2:
                    # Two words or less - put each on separate line
                    for word in words:
                        word_width = stringWidth(word, "Helvetica-Bold", 14)
                        pdf.drawString((SIDEBAR_WIDTH - word_width)/2, y, word)
                        y -= 0.8*cm
                    y -= 1.2*cm
                else:
                    # Multiple words - group intelligently
                    lines = []
                    current_line = ""
                    
                    for word in words:
                        test_line = f"{current_line} {word}".strip()
                        if stringWidth(test_line, "Helvetica-Bold", 14) <= max_width:
                            current_line = test_line
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = word
                    
                    if current_line:
                        lines.append(current_line)
                    
                    # Draw each line centered
                    for line in lines:
                        line_width = stringWidth(line, "Helvetica-Bold", 14)
                        pdf.drawString((SIDEBAR_WIDTH - line_width)/2, y, line)
                        y -= 0.8*cm
                    y -= 1.2*cm

    # Contact section with modern styling
    if data:
        y -= 0.5*cm
        
        # Section header with red background
        pdf.setFillColor(COLORS['primary'])
        pdf.rect(0.3*cm, y-0.3*cm, SIDEBAR_WIDTH-0.6*cm, 0.8*cm, fill=1)
        
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(COLORS['white'])
        pdf.drawString(0.7*cm, y, "CONTATO")
        y -= 1.2*cm
        
        # Contact items with better spacing and icons
        contact_items = [
            ('email', data.get('email')),
            ('telefone', data.get('telefone')),
            ('endereco', data.get('endereco')),
            ('linkedin', data.get('linkedin')),
            ('github', data.get('github'))
        ]
        
        for key, value in contact_items:
            if value:
                # Small yellow accent dot
                pdf.setFillColor(COLORS['secondary'])
                pdf.circle(0.7*cm, y+0.15*cm, 0.08*cm, fill=1)
                
                pdf.setFont("Helvetica", 9)
                pdf.setFillColor(COLORS['white'])
                pdf.drawString(1.2*cm, y, value)
                y -= 0.7*cm

def draw_section_header(pdf, title, y, x=None, colors_palette=None):
    COLORS = colors_palette or get_colors()
    
    if x is None:
        x = SIDEBAR_WIDTH + 1*cm
    
    # Title text in primary color
    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(COLORS['primary'])
    pdf.drawString(x, y, title)
    
    # Horizontal line below title
    pdf.setStrokeColor(COLORS['primary'])
    pdf.setLineWidth(1)
    title_width = stringWidth(title, "Helvetica-Bold", 14)
    pdf.line(x, y-0.3*cm, x + title_width + 1*cm, y-0.3*cm)
    
    return y - 1*cm

def draw_experience_item(pdf, experience_text, x, y, max_width, colors_palette=None):
    COLORS = colors_palette or get_colors()
    
    parts = experience_text.strip().split('|')
    if len(parts) >= 2:
        position = parts[0].strip()
        company_period = ' | '.join(parts[1:]).strip()
        
        # Position title in red
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(COLORS['primary'])
        y = draw_wrapped_text(pdf, position, x, y, max_width, font_name="Helvetica-Bold", font_size=12, color=COLORS['primary'], colors_palette=COLORS)
        
        # Company and period in smaller text
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(COLORS['muted'])
        y = draw_wrapped_text(pdf, company_period, x, y, max_width, font_name="Helvetica", font_size=10, color=COLORS['muted'], colors_palette=COLORS)
        
        # Subtle separator line
        pdf.setStrokeColor(COLORS['border'])
        pdf.setLineWidth(0.5)
        pdf.line(x, y-0.3*cm, x+max_width*0.3, y-0.3*cm)
        
    return y - 0.8*cm

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/gerar', methods=['POST'])
def gerar():
    data = {}
    campos = ['nome','email','telefone','endereco','linkedin','github',
              'resumo','habilidades','escolaridade','cursos','certificacoes','projetos','paleta']
    for campo in campos:
        data[campo] = request.form.get(campo, '')

    experiencias = []
    i = 1
    while True:
        empresa = request.form.get(f'empresa{i}', '').strip()
        cargo = request.form.get(f'cargo{i}', '').strip()
        periodo = request.form.get(f'periodo{i}', '').strip()
        responsabilidades = request.form.get(f'responsabilidades{i}', '').strip()
        conquistas = request.form.get(f'conquistas{i}', '').strip()
        
        # If no data for this experience, stop looking for more
        if not (empresa or cargo or responsabilidades or conquistas):
            break
            
        if empresa or cargo:  # If at least company or position is filled
            exp_text = ""
            if empresa and cargo and periodo:
                exp_text += f"{empresa} - {cargo} ({periodo})\n"
            elif empresa and cargo:
                exp_text += f"{empresa} - {cargo}\n"
            elif empresa:
                exp_text += f"{empresa}\n"
            
            if responsabilidades:
                # Split responsibilities by lines and add bullets
                resp_lines = [line.strip() for line in responsabilidades.split('\n') if line.strip()]
                for resp in resp_lines:
                    if not resp.startswith('•'):
                        exp_text += f"• {resp}\n"
                    else:
                        exp_text += f"{resp}\n"
            
            if conquistas:
                # Split achievements by lines and add bullets
                conq_lines = [line.strip() for line in conquistas.split('\n') if line.strip()]
                for conq in conq_lines:
                    if not conq.startswith('•'):
                        exp_text += f"• {conq}\n"
                    else:
                        exp_text += f"{conq}\n"
            
            if exp_text:
                experiencias.append(exp_text.strip())
        
        i += 1
    
    # Join all experiences with double newlines
    data['experiencia'] = '\n\n'.join(experiencias)

    print(f"[DEBUG] Processed {len(experiencias)} dynamic experiences")
    print(f"[DEBUG] Final experiencia data: '{data['experiencia'][:100]}...'")

    foto_path = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            foto_path = create_circle_image(filepath)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    
    pdf.setTitle(f"Currículo Profissional - {data.get('nome', 'Candidato')}")
    pdf.setAuthor(data.get('nome', ''))
    pdf.setSubject("Currículo Profissional - Desenvolvido com Design Moderno")

    selected_palette = data.get('paleta', 'professional')
    COLORS = get_colors(selected_palette)

    draw_sidebar(pdf, foto_path=foto_path, data=data, colors_palette=COLORS)
    y_content = MARGIN_TOP

    seccoes = [
        ('Resumo Profissional', 'resumo'),
        ('Habilidades Técnicas', 'habilidades'),
        ('Experiência Profissional', 'experiencia'),
        ('Formação Acadêmica', 'escolaridade'),
        ('Cursos Complementares', 'cursos'),
        ('Certificações', 'certificacoes'),
        ('Projetos Relevantes', 'projetos')
    ]

    for titulo, campo in seccoes:
        if data[campo]:
            print(f"[DEBUG] Processing section {titulo}: '{data[campo][:50]}...'")
            
            y_content = draw_section_header(pdf, titulo, y_content, colors_palette=COLORS)
            
            if campo == 'habilidades':
                skills = [skill.strip() for skill in data[campo].split(',') if skill.strip()]
                for skill in skills:
                    # Yellow bullet point aligned with text baseline
                    pdf.setFillColor(COLORS['secondary'])
                    pdf.circle(SIDEBAR_WIDTH + 1.3*cm, y_content + 0.15*cm, 0.1*cm, fill=1)
                    
                    pdf.setFont("Helvetica", 11)
                    pdf.setFillColor(COLORS['text'])
                    pdf.drawString(SIDEBAR_WIDTH + 1.8*cm, y_content, skill)
                    y_content -= 0.6*cm
            
            elif campo == 'experiencia':
                print(f"[DEBUG] Processing structured experiencia content")
                
                # Split by double newlines (each experience block)
                experience_blocks = [exp.strip() for exp in data[campo].split('\n\n') if exp.strip()]
                print(f"[DEBUG] Found {len(experience_blocks)} experience blocks")
                
                for i, exp_block in enumerate(experience_blocks):
                    if exp_block:
                        print(f"[DEBUG] Processing experience block {i+1}")
                        
                        lines = exp_block.split('\n')
                        header_line = lines[0] if lines else ""
                        
                        if header_line and not header_line.startswith('•'):
                            pdf.setFont("Helvetica-Bold", 12)
                            pdf.setFillColor(COLORS['text'])  # Use text color instead of primary
                            y_content = draw_wrapped_text(pdf, header_line, SIDEBAR_WIDTH + 1*cm, y_content, CONTENT_WIDTH, 
                                                        font_name="Helvetica-Bold", font_size=12, color=COLORS['text'], colors_palette=COLORS)
                            y_content -= 0.8*cm
                        
                        for line in lines[1:]:
                            if line.strip() and line.strip().startswith('•'):
                                bullet_text = line.strip()[1:].strip()  # Remove bullet and trim
                                
                                # Calculate text wrapping first to get proper bullet position
                                pdf.setFont("Helvetica", 11)
                                words = bullet_text.split()
                                text_lines = []
                                current_line = ""
                                text_width = CONTENT_WIDTH - 0.8*cm
                                
                                for word in words:
                                    test_line = f"{current_line} {word}".strip()
                                    if stringWidth(test_line, "Helvetica", 11) > text_width:
                                        if current_line:
                                            text_lines.append(current_line)
                                        current_line = word
                                    else:
                                        current_line = test_line
                                
                                if current_line:
                                    text_lines.append(current_line)
                                
                                # Draw bullet aligned with first line of text
                                if text_lines:
                                    pdf.setFillColor(COLORS['secondary'])
                                    pdf.circle(SIDEBAR_WIDTH + 1.3*cm, y_content + 0.1*cm, 0.08*cm, fill=1)
                                    
                                    pdf.setFillColor(COLORS['text'])
                                    for j, text_line in enumerate(text_lines):
                                        pdf.drawString(SIDEBAR_WIDTH + 1.8*cm, y_content, text_line)
                                        y_content -= 16  # Line height
                                    
                                    y_content -= 0.2*cm  # Extra space after bullet item
                        
                        y_content -= 0.8*cm  # Space between experience blocks
            
            else:
                y_content = draw_wrapped_text(pdf, data[campo], SIDEBAR_WIDTH + 1*cm, y_content, CONTENT_WIDTH, font_size=11, line_height=18, color=COLORS['text'], colors_palette=COLORS)

            y_content -= 1*cm
        else:
            print(f"[DEBUG] Section {titulo} is empty or None")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"curriculo_profissional_{data['nome'].replace(' ', '_')}.pdf", mimetype='application/pdf')

def get_colors(palette_name='professional'):
    return COLOR_PALETTES.get(palette_name, COLOR_PALETTES['professional'])

if __name__ == '__main__':
    app.run(debug=True)
