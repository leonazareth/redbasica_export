<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="pt_BR" sourcelanguage="en">
<context>
    <name>RedBasicaExport</name>
    
    <!-- Field Display Names -->
    <message>
        <source>Pipe Identifier</source>
        <translation>Identificador da Tubulação</translation>
    </message>
    <message>
        <source>Upstream Node</source>
        <translation>Nó de Montante</translation>
    </message>
    <message>
        <source>Downstream Node</source>
        <translation>Nó de Jusante</translation>
    </message>
    <message>
        <source>Length</source>
        <translation>Comprimento</translation>
    </message>
    <message>
        <source>Diameter</source>
        <translation>Diâmetro</translation>
    </message>
    <message>
        <source>Upstream Invert</source>
        <translation>Cota de Fundo Montante</translation>
    </message>
    <message>
        <source>Downstream Invert</source>
        <translation>Cota de Fundo Jusante</translation>
    </message>
    <message>
        <source>Upstream Ground</source>
        <translation>Cota do Terreno Montante</translation>
    </message>
    <message>
        <source>Downstream Ground</source>
        <translation>Cota do Terreno Jusante</translation>
    </message>
    <message>
        <source>Slope</source>
        <translation>Declividade</translation>
    </message>
    <message>
        <source>Material</source>
        <translation>Material</translation>
    </message>
    <message>
        <source>Notes</source>
        <translation>Observações</translation>
    </message>
    <message>
        <source>Node Identifier</source>
        <translation>Identificador do Nó</translation>
    </message>
    <message>
        <source>Ground Elevation</source>
        <translation>Cota do Terreno</translation>
    </message>
    <message>
        <source>Invert Elevation</source>
        <translation>Cota de Fundo</translation>
    </message>
    <message>
        <source>Upstream Depth</source>
        <translation>Profundidade Montante</translation>
    </message>
    <message>
        <source>Downstream Depth</source>
        <translation>Profundidade Jusante</translation>
    </message>
    <message>
        <source>Calculated Slope</source>
        <translation>Declividade Calculada</translation>
    </message>
    
    <!-- Field Descriptions -->
    <message>
        <source>Unique identifier for each pipe segment</source>
        <translation>Identificador único para cada segmento de tubulação</translation>
    </message>
    <message>
        <source>Identifier of upstream manhole or junction</source>
        <translation>Identificador do poço de visita ou junção de montante</translation>
    </message>
    <message>
        <source>Identifier of downstream manhole or junction</source>
        <translation>Identificador do poço de visita ou junção de jusante</translation>
    </message>
    <message>
        <source>Pipe length in meters</source>
        <translation>Comprimento da tubulação em metros</translation>
    </message>
    <message>
        <source>Pipe diameter in millimeters</source>
        <translation>Diâmetro da tubulação em milímetros</translation>
    </message>
    <message>
        <source>Upstream invert elevation in meters</source>
        <translation>Cota de fundo de montante em metros</translation>
    </message>
    <message>
        <source>Downstream invert elevation in meters</source>
        <translation>Cota de fundo de jusante em metros</translation>
    </message>
    <message>
        <source>Upstream ground surface elevation in meters</source>
        <translation>Cota da superfície do terreno de montante em metros</translation>
    </message>
    <message>
        <source>Downstream ground surface elevation in meters</source>
        <translation>Cota da superfície do terreno de jusante em metros</translation>
    </message>
    <message>
        <source>Pipe slope in meters per meter (m/m)</source>
        <translation>Declividade da tubulação em metros por metro (m/m)</translation>
    </message>
    <message>
        <source>Pipe material (e.g., PVC, concrete, etc.)</source>
        <translation>Material da tubulação (ex: PVC, concreto, etc.)</translation>
    </message>
    <message>
        <source>Additional notes or observations</source>
        <translation>Observações ou notas adicionais</translation>
    </message>
    <message>
        <source>Unique identifier for each junction or manhole</source>
        <translation>Identificador único para cada junção ou poço de visita</translation>
    </message>
    <message>
        <source>Ground surface elevation at junction in meters</source>
        <translation>Cota da superfície do terreno na junção em metros</translation>
    </message>
    <message>
        <source>Junction invert elevation in meters</source>
        <translation>Cota de fundo da junção em metros</translation>
    </message>
    <message>
        <source>Calculated depth at upstream end (ground - invert)</source>
        <translation>Profundidade calculada na extremidade de montante (terreno - fundo)</translation>
    </message>
    <message>
        <source>Calculated depth at downstream end (ground - invert)</source>
        <translation>Profundidade calculada na extremidade de jusante (terreno - fundo)</translation>
    </message>
    <message>
        <source>Calculated slope from elevation difference and length</source>
        <translation>Declividade calculada a partir da diferença de elevação e comprimento</translation>
    </message>
    
    <!-- Error Messages -->
    <message>
        <source>Layer "{layer_name}" not found in project</source>
        <translation>Camada "{layer_name}" não encontrada no projeto</translation>
    </message>
    <message>
        <source>Layer "{layer_name}" has invalid geometry type. Expected: {expected}, Found: {found}</source>
        <translation>Camada "{layer_name}" possui tipo de geometria inválido. Esperado: {expected}, Encontrado: {found}</translation>
    </message>
    <message>
        <source>Layer "{layer_name}" contains no features</source>
        <translation>Camada "{layer_name}" não contém feições</translation>
    </message>
    <message>
        <source>Layer "{layer_name}" is missing required fields: {fields}</source>
        <translation>Camada "{layer_name}" não possui os campos obrigatórios: {fields}</translation>
    </message>
    <message>
        <source>Required field "{field_name}" is not mapped</source>
        <translation>Campo obrigatório "{field_name}" não está mapeado</translation>
    </message>
    <message>
        <source>Field "{field_name}" is mapped to non-existent layer field "{layer_field}"</source>
        <translation>Campo "{field_name}" está mapeado para o campo inexistente "{layer_field}" da camada</translation>
    </message>
    <message>
        <source>Failed to convert value "{value}" to {target_type} for field "{field_name}"</source>
        <translation>Falha ao converter valor "{value}" para {target_type} no campo "{field_name}"</translation>
    </message>
    <message>
        <source>Output path is invalid or not writable: {path}</source>
        <translation>Caminho de saída é inválido ou não permite escrita: {path}</translation>
    </message>
    <message>
        <source>Template file not found: {template_path}</source>
        <translation>Arquivo de modelo não encontrado: {template_path}</translation>
    </message>
    <message>
        <source>Failed to create DXF file: {error}</source>
        <translation>Falha ao criar arquivo DXF: {error}</translation>
    </message>
    <message>
        <source>Failed to process geometry for feature {feature_id}: {error}</source>
        <translation>Falha ao processar geometria da feição {feature_id}: {error}</translation>
    </message>
    <message>
        <source>Required dependency not available: {dependency}</source>
        <translation>Dependência obrigatória não disponível: {dependency}</translation>
    </message>
    <message>
        <source>Permission denied accessing file: {file_path}</source>
        <translation>Permissão negada ao acessar arquivo: {file_path}</translation>
    </message>
    <message>
        <source>An unexpected error occurred: {error}</source>
        <translation>Ocorreu um erro inesperado: {error}</translation>
    </message>
    
    <!-- UI Text -->
    <message>
        <source>Flexible Sewerage Network DXF Export</source>
        <translation>Exportação Flexível de Rede de Esgoto para DXF</translation>
    </message>
    <message>
        <source>Select Layer</source>
        <translation>Selecionar Camada</translation>
    </message>
    <message>
        <source>Configure Field Mapping</source>
        <translation>Configurar Mapeamento de Campos</translation>
    </message>
    <message>
        <source>Layer Selection</source>
        <translation>Seleção de Camadas</translation>
    </message>
    <message>
        <source>Export Options</source>
        <translation>Opções de Exportação</translation>
    </message>
    <message>
        <source>Advanced Options</source>
        <translation>Opções Avançadas</translation>
    </message>
    <message>
        <source>Validation Results</source>
        <translation>Resultados da Validação</translation>
    </message>
    <message>
        <source>Pipes Layer:</source>
        <translation>Camada de Tubulações:</translation>
    </message>
    <message>
        <source>Junctions Layer:</source>
        <translation>Camada de Junções:</translation>
    </message>
    <message>
        <source>Output File:</source>
        <translation>Arquivo de Saída:</translation>
    </message>
    <message>
        <source>Scale Factor:</source>
        <translation>Fator de Escala:</translation>
    </message>
    <message>
        <source>Layer Prefix:</source>
        <translation>Prefixo das Camadas:</translation>
    </message>
    <message>
        <source>Template File:</source>
        <translation>Arquivo de Modelo:</translation>
    </message>
    <message>
        <source>Configure Fields...</source>
        <translation>Configurar Campos...</translation>
    </message>
    <message>
        <source>Browse...</source>
        <translation>Procurar...</translation>
    </message>
    <message>
        <source>Export</source>
        <translation>Exportar</translation>
    </message>
    <message>
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <source>OK</source>
        <translation>OK</translation>
    </message>
    <message>
        <source>Apply</source>
        <translation>Aplicar</translation>
    </message>
    <message>
        <source>Reset</source>
        <translation>Redefinir</translation>
    </message>
    <message>
        <source>Auto Map</source>
        <translation>Mapear Automaticamente</translation>
    </message>
    <message>
        <source>Include flow arrows</source>
        <translation>Incluir setas de fluxo</translation>
    </message>
    <message>
        <source>Include pipe labels</source>
        <translation>Incluir rótulos das tubulações</translation>
    </message>
    <message>
        <source>Include elevation data</source>
        <translation>Incluir dados de elevação</translation>
    </message>
    <message>
        <source>Use custom template</source>
        <translation>Usar modelo personalizado</translation>
    </message>
    <message>
        <source>Validation passed - ready to export</source>
        <translation>Validação aprovada - pronto para exportar</translation>
    </message>
    <message>
        <source>Validation failed - please fix errors</source>
        <translation>Validação falhou - por favor corrija os erros</translation>
    </message>
    <message>
        <source>Exporting sewerage network...</source>
        <translation>Exportando rede de esgoto...</translation>
    </message>
    <message>
        <source>Export completed successfully</source>
        <translation>Exportação concluída com sucesso</translation>
    </message>
    <message>
        <source>Export failed</source>
        <translation>Exportação falhou</translation>
    </message>
    <message>
        <source>Select any line layer containing pipe/conduit data</source>
        <translation>Selecione qualquer camada de linhas contendo dados de tubulações/condutos</translation>
    </message>
    <message>
        <source>Select any point layer containing junction/manhole data</source>
        <translation>Selecione qualquer camada de pontos contendo dados de junções/poços de visita</translation>
    </message>
    <message>
        <source>Path where the DXF file will be saved</source>
        <translation>Caminho onde o arquivo DXF será salvo</translation>
    </message>
    <message>
        <source>Scale factor for text and symbol sizing</source>
        <translation>Fator de escala para dimensionamento de texto e símbolos</translation>
    </message>
    <message>
        <source>Prefix added to all DXF layer names</source>
        <translation>Prefixo adicionado a todos os nomes de camadas DXF</translation>
    </message>
    <message>
        <source>Optional DXF template file with predefined blocks and styles</source>
        <translation>Arquivo de modelo DXF opcional com blocos e estilos predefinidos</translation>
    </message>
    
    <!-- Plugin Menu Items -->
    <message>
        <source>&amp;RedBasica Export</source>
        <translation>&amp;RedBasica Export</translation>
    </message>
    <message>
        <source>Flexible Sewerage DXF Export</source>
        <translation>Exportação Flexível de Esgoto para DXF</translation>
    </message>
    <message>
        <source>Export Sewerage Network to DXF...</source>
        <translation>Exportar Rede de Esgoto para DXF...</translation>
    </message>
</context>
</TS>