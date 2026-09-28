# Roadmap de Desenvolvimento: AutoCroqui3D

## Fase 1: Fundação & Especificações [CONCLUÍDO]
- [x] Tarefa 1.1: Pesquisa arquitetural e levantamento de requisitos (`RESEARCH.md`, `REQUIREMENTS.md`)
- [x] Tarefa 1.2: Configuração do ambiente (Python portátil 3.11, bibliotecas de visão, PDF e COM)
- [x] Tarefa 1.3: Modelo de dados (Schema Pydantic) para árvores de operações CAD (`PartModel`, `Sketch`, `Extrude`, `Hole`, `Chamfer`, `Fillet`, `Revolve`)

## Fase 2: Motor de Ingestão e Visão Multimodal [CONCLUÍDO]
- [x] Tarefa 2.1: Módulo de ingestão de arquivos (PDF multipágina, PNG, JPG, TIFF, WEBP) com conversão de DPI e pré-processamento
- [x] Tarefa 2.2: Motor de interpretação multimodal de croquis e desenhos técnicos com prompts especializados em normas ABNT/ISO
- [x] Tarefa 2.3: Parser e validador de geometria para garantir viabilidade física 3D antes de modelar

## Fase 3: Conector Autodesk Inventor & Gerador iLogic [CONCLUÍDO]
- [x] Tarefa 3.1: Gerador de código iLogic autônomo (`.iLogicVb`) com suporte a templates métricos
- [x] Tarefa 3.2: Módulo COM direto para Autodesk Inventor (`win32com.client`) com criação de esboços, extrusões, cortes e furos em tempo real
- [x] Tarefa 3.3: Gerador de geometria 3D para pré-visualização (Three.js JSON / OBJ)

## Fase 4: Interface Web Interativa (Frontend & API) [CONCLUÍDO]
- [x] Tarefa 4.1: Servidor web leve e moderno (FastAPI) com endpoints para upload, análise, edição e exportação
- [x] Tarefa 4.2: Frontend com visualizador lado a lado (Croqui com cotas marcadas + Viewport 3D interativo Three.js)
- [x] Tarefa 4.3: Painel de ajuste fino paramétrico (editar cotas antes de disparar o Inventor)

## Fase 5: Testes, Validação e Documentação [CONCLUÍDO]
- [x] Tarefa 5.1: Testes unitários de parsing de cotas e geração de comandos CAD (10 testes passando)
- [x] Tarefa 5.2: Verificação de ponta a ponta da API e gerador de geometria
- [x] Tarefa 5.3: Guia passo a passo de uso com o Autodesk Inventor, executador `.bat` e `README.md`
