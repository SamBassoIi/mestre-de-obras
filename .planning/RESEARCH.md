# Research & Discovery: Sistema de Leitura de Croquis e Modelagem 3D Automática no Autodesk Inventor

## 1. Contexto e Desafios (Desenho Técnico Mecânico 2)
Na disciplina de Desenho Técnico Mecânico (DT2 / Desenho de Máquinas):
- **Fontes de Dados**:
  - Croquis feitos à mão livre (papel milimetrado, caderno, sulfite, fotos com iluminação irregular ou perspectiva distorcida).
  - Desenhos técnicos normalizados (PDFs vetoriais ou rasterizados, pranchas A4/A3 com margens, legendas/bloco de título).
  - Vistas ortográficas no 1º diedro (norma brasileira ABNT NBR 10067 / NBR 10126): Vista Frontal (VF), Vista Superior (VS), Vista Lateral Esquerda (VLE), Vistas Auxiliares.
  - Cortes e Seções: Corte Total A-A, Meio Corte, Corte em Desvio, Hachuras de material (ABNT NBR 12298).
  - Cotagem mecânica: Cotas lineares, diâmetros (Ø), raios (R), chanfros (ex: 2x45°), furos com escareado/rebaixo, roscas (M6, M8), tolerâncias dimensionais e geométricas básicas.

## 2. Por que Abordagens Tradicionais de OCR Falham
- OCR tradicional (Tesseract, EasyOCR) apenas detecta caracteres soltos no espaço (ex: "45", "100", "Ø12").
- Ele não sabe:
  1. A qual linha de cota o texto pertence.
  2. A qual aresta/vista a linha de chamada aponta.
  3. A correlação espacial 3D entre a Vista Frontal, Superior e Lateral.
  4. Como traduzir uma vista 2D em operações de modelagem paramétrica (Extrusão, Revolução, Furação, Chanfro, Arredondamento).

## 3. Abordagem Moderna: Visão Multimodal com IA (Gemini 2.5 / 1.5 Pro) + CAD Feature Tree
- A visão multimodal avançada analisa o desenho holística e semanticamente:
  1. Identificação do tipo de desenho (Peça prismática, cilíndrica/revolução, chapa/perfil ou mista).
  2. Identificação das vistas ortográficas e corte.
  3. Decomposição em **Árvore de Operações CAD (CAD Feature Tree)**:
     - **Base Feature**: ex. Sketch no plano XY (retângulo 120 x 80 mm) -> Extrusão de 25 mm.
     - **Secondary Features (Cuts / Pockets / Rebaixos)**: ex. Sketch na face superior -> retângulo de 40 x 30 mm -> Extrusão de corte (Cut) profundidade 10 mm.
     - **Hole Features**: furos simples, furos passantes com diâmetro Ø, localizados a partir de arestas de referência.
     - **Dress-up Features**: Raios de concordância (Fillets) nas arestas verticais e chanfros (Chamfers).
- Extração de saída estritamente estruturada via **JSON Schema Pydantic**.

## 4. Integração com Autodesk Inventor
Autodesk Inventor no Windows possui múltiplos métodos de automação:
1. **Autodesk Inventor COM API (`win32com.client` / .NET interop)**:
   - Acesso direto ao objeto COM `Inventor.Application`.
   - Pode conectar em uma sessão do Inventor aberta ou abrir uma nova sessão em segundo plano (`Visible = True/False`).
   - Métodos nativos:
     - `Documents.Add(DocumentTypeEnum.kPartDocumentObject)`
     - `ComponentDefinition.Sketches.Add(PlanarEntity)`
     - `Sketch.SketchLines.AddByTwoPoints(...)`, `Sketch.SketchCircles.AddByCenterRadius(...)`
     - `Features.ExtrudeFeatures.AddDistanceExtend(...)`
     - `Features.HoleFeatures.AddDrilledByDistanceExtend(...)`
     - `Features.FilletFeatures`, `Features.ChamferFeatures`
     - Salva diretamente como `.ipt`, ou exporta para `.step`, `.sat`, `.stl`.
2. **Autodesk Inventor iLogic Scripting (`.iLogicVb`)**:
   - Geração de scripts iLogic de alta legibilidade e manutenibilidade.
   - Permite que o estudante leve o código para qualquer máquina com Inventor (laboratório da faculdade, notebook) e rode a regra com 1 clique (`Manage -> Add Rule -> Run Rule`).
   - Não depende de registro de bibliotecas COM na máquina de análise.
3. **Pré-visualização 3D Universal no Navegador (Three.js)**:
   - Renderização interativa imediata no navegador (Web UI), permitindo que o usuário gire, dê zoom, inspecione as medidas e valide o modelo antes mesmo de disparar o Inventor!

## 5. Interface com o Usuário
- Interface web rica e moderna:
  - Drag-and-drop para PDFs (todas as páginas convertidas automaticamente em alta resolução) e imagens (JPG, PNG, WEBP, etc.).
  - Visualização lado a lado: Croqui Original com anotações de cotas identificadas vs. Visualizador 3D em tempo real.
  - Painel de inspeção e edição das cotas: o usuário pode ajustar qualquer medida antes de modelar.
  - Botões de exportação: "Modelar no Inventor (COM direto)", "Baixar Script iLogic (.iLogicVb)", "Baixar JSON de Geometria CAD", "Exportar STEP/OBJ".
