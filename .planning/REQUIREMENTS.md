# Requisitos do Sistema: AutoCroqui3D (Croqui2Inventor)

## 1. Visão Geral
Sistema inteligente capaz de ingerir desenhos técnicos de engenharia mecânica (croquis à mão livre, desenhos técnicos normalizados, PDFs de exercícios acadêmicos e imagens digitalizadas), interpretar semanticamente suas cotas, vistas ortográficas e geometria 3D, e gerar a peça modelada no Autodesk Inventor (via COM API direta e scripts iLogic portáveis), além de disponibilizar visualização 3D interativa no navegador.

## 2. Requisitos Funcionais (RF)

### RF01 - Ingestão Multiformato
- O sistema deve aceitar arquivos nos formatos: PDF (páginas únicas ou múltiplas), PNG, JPG, JPEG, WEBP, BMP.
- Para PDFs multipáginas, permitir selecionar a página do exercício ou analisar todas as páginas.
- Pré-processamento automático: normalização de resolução, rotação, realce de contraste para croquis claros ou com sombras.

### RF02 - Interpretação Semântica e Geométrica com IA Multimodal
- Extrair o bloco de título / legenda (nome da peça, escala, material, unidade padrão mm).
- Identificar as vistas presentes (Vista Frontal, Superior, Lateral, Isométrica, Cortes A-A, Detalhes).
- Interpretar todas as cotas e dimensões nominais:
  - Dimensões lineares (comprimento, largura, altura, distâncias entre centros).
  - Diâmetros ($\varnothing$) e raios ($R$).
  - Tipos de furo (passante, cego com profundidade, escareado, rebaixado).
  - Chanfros (distância x ângulo, ex: 2x45°).
  - Raios de arredondamento / concordância (fillets).
  - Geometrias de revolução (eixos cilíndricos escalonados, canais de anel).
- Estruturar a peça em uma sequência paramétrica de modelagem CAD (**CAD Feature Tree**):
  - Sketches 2D definidos por perfis (retângulos, círculos, polígonos, contornos fechados).
  - Operações de Extrusão (Adição / Subtração / Join / Cut) com profundidades exatas.
  - Furos (Holes) com posicionamento relativo e diâmetros.
  - Features de acabamento (Chanfros e Concordâncias).

### RF03 - Validação e Edição de Medidas pelo Usuário
- Interface com tabela interativa de cotas e operações identificadas.
- O usuário pode revisar, editar valores ou adicionar detalhes antes de enviar para o Inventor.
- Visualização lado a lado da imagem enviada e das medidas extraídas.

### RF04 - Integração e Modelagem no Autodesk Inventor
- **Modo 1 - Conexão Direta COM (Autodesk Inventor COM API)**:
  - Comunica-se com o Inventor aberto na máquina via `win32com.client`.
  - Cria um novo arquivo de peça (`.ipt`) usando o template métrico padrão (`Standard (mm).ipt`).
  - Executa a árvore de modelagem paramétrica (esboços 2D, extrusões, cortes, furos, chanfros).
  - Atualiza a visualização no Inventor e permite salvar o arquivo.
- **Modo 2 - Gerador de Regra iLogic Portável (`.iLogicVb`)**:
  - Gera script iLogic pronto para ser colado ou importado diretamente no Inventor de qualquer computador (mesmo sem Python instalado na máquina de destino).
  - Código limpo, comentado e 100% nativo da API do Inventor.

### RF05 - Pré-visualização 3D em Tempo Real
- Renderização 3D interativa no navegador (Three.js):
  - Órbita 360°, zoom, pan, modo sombreado e modo arestas visíveis (wireframe/edges).
  - Medições de referência no próprio modelo 3D.
  - Exportação direta de arquivo 3D genérico (OBJ / STL / STEP) para visualização rápida.

## 3. Requisitos Não Funcionais (RNF)
- **RNF01 - Robustez a Croquis Irregulares**: Capacidade de lidar com fotos com ângulo levemente inclinado, traços de grafite ou caneta.
- **RNF02 - Usabilidade**: Interface web limpa, intuitiva, em português, acessível localmente via navegador (`http://localhost:8000`).
- **RNF03 - Desacoplamento**: O sistema deve funcionar mesmo se o Autodesk Inventor não estiver rodando no momento da interpretação (gerando o script e visualizador 3D para posterior uso no Inventor).
