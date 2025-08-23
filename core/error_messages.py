"""
Multilingual error messages and user-friendly message generation.

This module provides internationalized error messages with suggested solutions
for the Flexible Sewerage DXF Export Plugin.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from .i18n_manager import tr


class MessageLanguage(Enum):
    """Supported languages for error messages."""
    ENGLISH = "en"
    PORTUGUESE = "pt"
    SPANISH = "es"


class ErrorMessageCatalog:
    """Catalog of error messages in multiple languages."""
    
    def __init__(self, default_language: MessageLanguage = MessageLanguage.ENGLISH):
        """
        Initialize error message catalog.
        
        Args:
            default_language: Default language for messages
        """
        self.default_language = default_language
        self.messages = self._initialize_messages()
    
    def _initialize_messages(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Initialize the complete message catalog."""
        return {
            # Layer validation messages
            "layer_invalid": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Layer '{layer_name}' is not valid or accessible",
                    "suggestions": [
                        "Check that the layer is properly loaded in QGIS",
                        "Verify the layer data source is accessible",
                        "Try reloading the layer from its original source"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Camada '{layer_name}' não é válida ou acessível",
                    "suggestions": [
                        "Verifique se a camada está carregada corretamente no QGIS",
                        "Verifique se a fonte de dados da camada está acessível",
                        "Tente recarregar a camada da fonte original"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "La capa '{layer_name}' no es válida o accesible",
                    "suggestions": [
                        "Verifique que la capa esté cargada correctamente en QGIS",
                        "Verifique que la fuente de datos de la capa sea accesible",
                        "Intente recargar la capa desde su fuente original"
                    ]
                }
            },
            
            "geometry_type_mismatch": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Layer '{layer_name}' has {actual_type} geometry, but {required_type} is required",
                    "suggestions": [
                        "Select a layer with {required_type} geometry type",
                        "Check the layer properties to verify geometry type",
                        "Use QGIS processing tools to convert geometry if needed"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Camada '{layer_name}' tem geometria {actual_type}, mas {required_type} é necessário",
                    "suggestions": [
                        "Selecione uma camada com tipo de geometria {required_type}",
                        "Verifique as propriedades da camada para confirmar o tipo de geometria",
                        "Use ferramentas de processamento do QGIS para converter geometria se necessário"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "La capa '{layer_name}' tiene geometría {actual_type}, pero se requiere {required_type}",
                    "suggestions": [
                        "Seleccione una capa con tipo de geometría {required_type}",
                        "Verifique las propiedades de la capa para confirmar el tipo de geometría",
                        "Use herramientas de procesamiento de QGIS para convertir geometría si es necesario"
                    ]
                }
            },
            
            "missing_required_fields": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Required fields are not mapped: {missing_fields}",
                    "suggestions": [
                        "Map the missing fields using the attribute mapper dialog",
                        "Set default values for unmapped required fields",
                        "Use the auto-mapping feature to suggest field mappings"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Campos obrigatórios não estão mapeados: {missing_fields}",
                    "suggestions": [
                        "Mapeie os campos ausentes usando o diálogo de mapeamento de atributos",
                        "Defina valores padrão para campos obrigatórios não mapeados",
                        "Use o recurso de mapeamento automático para sugerir mapeamentos de campos"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "Los campos requeridos no están mapeados: {missing_fields}",
                    "suggestions": [
                        "Mapee los campos faltantes usando el diálogo de mapeo de atributos",
                        "Establezca valores predeterminados para campos requeridos no mapeados",
                        "Use la función de mapeo automático para sugerir mapeos de campos"
                    ]
                }
            },
            
            "field_not_found": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Mapped field '{field_name}' not found in layer '{layer_name}'",
                    "suggestions": [
                        "Check that the field name is spelled correctly",
                        "Verify the field exists in the layer attribute table",
                        "Update the field mapping to use an existing field"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Campo mapeado '{field_name}' não encontrado na camada '{layer_name}'",
                    "suggestions": [
                        "Verifique se o nome do campo está escrito corretamente",
                        "Verifique se o campo existe na tabela de atributos da camada",
                        "Atualize o mapeamento do campo para usar um campo existente"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "Campo mapeado '{field_name}' no encontrado en la capa '{layer_name}'",
                    "suggestions": [
                        "Verifique que el nombre del campo esté escrito correctamente",
                        "Verifique que el campo existe en la tabla de atributos de la capa",
                        "Actualice el mapeo del campo para usar un campo existente"
                    ]
                }
            },
            
            # File operation messages
            "file_permission_denied": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Cannot {operation} file: {file_path}. Permission denied.",
                    "suggestions": [
                        "Check that you have {operation} permissions to the file/directory",
                        "Ensure the file is not open in another application",
                        "Try selecting a different output location",
                        "Run QGIS as administrator if necessary"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Não é possível {operation} arquivo: {file_path}. Permissão negada.",
                    "suggestions": [
                        "Verifique se você tem permissões de {operation} para o arquivo/diretório",
                        "Certifique-se de que o arquivo não está aberto em outro aplicativo",
                        "Tente selecionar um local de saída diferente",
                        "Execute o QGIS como administrador se necessário"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "No se puede {operation} archivo: {file_path}. Permiso denegado.",
                    "suggestions": [
                        "Verifique que tiene permisos de {operation} para el archivo/directorio",
                        "Asegúrese de que el archivo no esté abierto en otra aplicación",
                        "Intente seleccionar una ubicación de salida diferente",
                        "Ejecute QGIS como administrador si es necesario"
                    ]
                }
            },
            
            "template_not_found": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Template file not found: {template_path}",
                    "suggestions": [
                        "Check that the template file path is correct",
                        "Verify the template file exists and is accessible",
                        "Use the default template instead",
                        "Select a different template file"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Arquivo de modelo não encontrado: {template_path}",
                    "suggestions": [
                        "Verifique se o caminho do arquivo de modelo está correto",
                        "Verifique se o arquivo de modelo existe e está acessível",
                        "Use o modelo padrão em vez disso",
                        "Selecione um arquivo de modelo diferente"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "Archivo de plantilla no encontrado: {template_path}",
                    "suggestions": [
                        "Verifique que la ruta del archivo de plantilla sea correcta",
                        "Verifique que el archivo de plantilla existe y es accesible",
                        "Use la plantilla predeterminada en su lugar",
                        "Seleccione un archivo de plantilla diferente"
                    ]
                }
            },
            
            # Export operation messages
            "export_failed": {
                MessageLanguage.ENGLISH.value: {
                    "message": "DXF export failed: {error_details}",
                    "suggestions": [
                        "Check the export configuration and try again",
                        "Verify all required fields are properly mapped",
                        "Ensure the output path is writable",
                        "Check QGIS message log for detailed error information"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Falha na exportação DXF: {error_details}",
                    "suggestions": [
                        "Verifique a configuração de exportação e tente novamente",
                        "Verifique se todos os campos obrigatórios estão mapeados corretamente",
                        "Certifique-se de que o caminho de saída é gravável",
                        "Verifique o log de mensagens do QGIS para informações detalhadas do erro"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "Falló la exportación DXF: {error_details}",
                    "suggestions": [
                        "Verifique la configuración de exportación e intente nuevamente",
                        "Verifique que todos los campos requeridos estén mapeados correctamente",
                        "Asegúrese de que la ruta de salida sea escribible",
                        "Verifique el registro de mensajes de QGIS para información detallada del error"
                    ]
                }
            },
            
            "geometry_invalid": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Invalid geometry in feature {feature_id}: {geometry_issue}",
                    "suggestions": [
                        "Use QGIS geometry validation tools to fix the geometry",
                        "Check the feature in the attribute table and map view",
                        "Consider excluding invalid features from export",
                        "Verify the coordinate reference system is correct"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Geometria inválida na feição {feature_id}: {geometry_issue}",
                    "suggestions": [
                        "Use ferramentas de validação de geometria do QGIS para corrigir a geometria",
                        "Verifique a feição na tabela de atributos e visualização do mapa",
                        "Considere excluir feições inválidas da exportação",
                        "Verifique se o sistema de referência de coordenadas está correto"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "Geometría inválida en la característica {feature_id}: {geometry_issue}",
                    "suggestions": [
                        "Use herramientas de validación de geometría de QGIS para corregir la geometría",
                        "Verifique la característica en la tabla de atributos y vista del mapa",
                        "Considere excluir características inválidas de la exportación",
                        "Verifique que el sistema de referencia de coordenadas sea correcto"
                    ]
                }
            },
            
            # Data conversion messages
            "data_conversion_failed": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Failed to convert data in field '{field_name}': {value} -> {target_type}",
                    "suggestions": [
                        "Check the data format in the source field",
                        "Verify numeric fields contain valid numbers",
                        "Consider setting a default value for this field",
                        "Use QGIS field calculator to clean the data"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Falha ao converter dados no campo '{field_name}': {value} -> {target_type}",
                    "suggestions": [
                        "Verifique o formato dos dados no campo de origem",
                        "Verifique se campos numéricos contêm números válidos",
                        "Considere definir um valor padrão para este campo",
                        "Use a calculadora de campo do QGIS para limpar os dados"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "Error al convertir datos en el campo '{field_name}': {value} -> {target_type}",
                    "suggestions": [
                        "Verifique el formato de los datos en el campo fuente",
                        "Verifique que los campos numéricos contengan números válidos",
                        "Considere establecer un valor predeterminado para este campo",
                        "Use la calculadora de campo de QGIS para limpiar los datos"
                    ]
                }
            },
            
            "validation_failed": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Configuration validation failed",
                    "suggestions": [
                        "Check that all required fields are mapped or have default values",
                        "Verify that selected layers have the correct geometry type",
                        "Ensure all field mappings point to existing layer fields",
                        "Review the validation messages for specific issues"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Falha na validação da configuração",
                    "suggestions": [
                        "Verifique se todos os campos obrigatórios estão mapeados ou têm valores padrão",
                        "Verifique se as camadas selecionadas têm o tipo de geometria correto",
                        "Certifique-se de que todos os mapeamentos de campo apontem para campos de camada existentes",
                        "Revise as mensagens de validação para problemas específicos"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "Falló la validación de configuración",
                    "suggestions": [
                        "Verifique que todos los campos requeridos estén mapeados o tengan valores predeterminados",
                        "Verifique que las capas seleccionadas tengan el tipo de geometría correcto",
                        "Asegúrese de que todos los mapeos de campo apunten a campos de capa existentes",
                        "Revise los mensajes de validación para problemas específicos"
                    ]
                }
            },
            
            # Dialog operation messages
            "mapping_dialog_failed": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Failed to open field mapping dialog: {error}",
                    "suggestions": [
                        "Check that the layer is properly selected and loaded",
                        "Verify the layer has accessible attribute fields",
                        "Try reselecting the layer and opening the dialog again",
                        "Check QGIS message log for detailed error information"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Falha ao abrir diálogo de mapeamento de campos: {error}",
                    "suggestions": [
                        "Verifique se a camada está selecionada e carregada corretamente",
                        "Verifique se a camada tem campos de atributos acessíveis",
                        "Tente reselecionar a camada e abrir o diálogo novamente",
                        "Verifique o log de mensagens do QGIS para informações detalhadas do erro"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "Error al abrir el diálogo de mapeo de campos: {error}",
                    "suggestions": [
                        "Verifique que la capa esté seleccionada y cargada correctamente",
                        "Verifique que la capa tenga campos de atributos accesibles",
                        "Intente reseleccionar la capa y abrir el diálogo nuevamente",
                        "Verifique el registro de mensajes de QGIS para información detallada del error"
                    ]
                }
            },
            
            # Progress and completion messages
            "export_completed_with_warnings": {
                MessageLanguage.ENGLISH.value: {
                    "message": "Export completed with {warning_count} warnings and {error_count} errors",
                    "suggestions": [
                        "Review the error log for details about issues encountered",
                        "Check the exported DXF file to verify completeness",
                        "Consider fixing data issues and re-exporting if needed"
                    ]
                },
                MessageLanguage.PORTUGUESE.value: {
                    "message": "Exportação concluída com {warning_count} avisos e {error_count} erros",
                    "suggestions": [
                        "Revise o log de erros para detalhes sobre problemas encontrados",
                        "Verifique o arquivo DXF exportado para verificar completude",
                        "Considere corrigir problemas de dados e re-exportar se necessário"
                    ]
                },
                MessageLanguage.SPANISH.value: {
                    "message": "Exportación completada con {warning_count} advertencias y {error_count} errores",
                    "suggestions": [
                        "Revise el registro de errores para detalles sobre problemas encontrados",
                        "Verifique el archivo DXF exportado para verificar completitud",
                        "Considere corregir problemas de datos y re-exportar si es necesario"
                    ]
                }
            }
        }
    
    def get_message(self, message_key: str, language: Optional[MessageLanguage] = None,
                   **format_args) -> Dict[str, Any]:
        """
        Get localized message with formatting.
        
        Args:
            message_key: Key identifying the message
            language: Target language (uses default if not specified)
            **format_args: Arguments for message formatting
            
        Returns:
            Dictionary with 'message' and 'suggestions' keys
        """
        if language is None:
            language = self.default_language
        
        # Get message template
        message_templates = self.messages.get(message_key, {})
        
        # Try requested language, fall back to English, then to first available
        lang_key = language.value
        if lang_key not in message_templates:
            lang_key = MessageLanguage.ENGLISH.value
        if lang_key not in message_templates:
            lang_key = next(iter(message_templates.keys())) if message_templates else None
        
        if not lang_key or lang_key not in message_templates:
            # Fallback message if key not found
            return {
                "message": f"Error message not found: {message_key}",
                "suggestions": ["Check the error log for more details"]
            }
        
        template = message_templates[lang_key]
        
        # Format message and suggestions
        try:
            formatted_message = template["message"].format(**format_args)
            formatted_suggestions = [
                suggestion.format(**format_args) for suggestion in template["suggestions"]
            ]
        except KeyError as e:
            # Handle missing format arguments
            formatted_message = f"{template['message']} (formatting error: missing {e})"
            formatted_suggestions = template["suggestions"]
        
        return {
            "message": formatted_message,
            "suggestions": formatted_suggestions
        }
    
    def set_default_language(self, language: MessageLanguage):
        """Set the default language for messages."""
        self.default_language = language


class UserFriendlyErrorFormatter:
    """Formats errors into user-friendly messages with suggestions."""
    
    def __init__(self, language: MessageLanguage = MessageLanguage.ENGLISH):
        """
        Initialize error formatter.
        
        Args:
            language: Language for error messages
        """
        self.catalog = ErrorMessageCatalog(language)
        self.language = language
    
    def format_layer_validation_error(self, layer_name: str, error_type: str,
                                    **kwargs) -> str:
        """Format layer validation error message."""
        message_data = self.catalog.get_message(error_type, self.language,
                                              layer_name=layer_name, **kwargs)
        return self._format_message_with_suggestions(message_data)
    
    def format_mapping_error(self, error_type: str, **kwargs) -> str:
        """Format field mapping error message."""
        message_data = self.catalog.get_message(error_type, self.language, **kwargs)
        return self._format_message_with_suggestions(message_data)
    
    def format_export_error(self, error_type: str, **kwargs) -> str:
        """Format export operation error message."""
        message_data = self.catalog.get_message(error_type, self.language, **kwargs)
        return self._format_message_with_suggestions(message_data)
    
    def format_file_error(self, error_type: str, **kwargs) -> str:
        """Format file operation error message."""
        message_data = self.catalog.get_message(error_type, self.language, **kwargs)
        return self._format_message_with_suggestions(message_data)
    
    def _format_message_with_suggestions(self, message_data: Dict[str, Any]) -> str:
        """Format message with suggestions into a single string."""
        message = message_data["message"]
        suggestions = message_data["suggestions"]
        
        if suggestions:
            suggestion_text = "\n".join(f"• {suggestion}" for suggestion in suggestions)
            return f"{message}\n\nSuggested solutions:\n{suggestion_text}"
        
        return message
    
    def format_progress_summary(self, processed: int, total: int, errors: int,
                              warnings: int) -> str:
        """Format progress summary message."""
        if errors == 0 and warnings == 0:
            if self.language == MessageLanguage.PORTUGUESE:
                return f"Exportação concluída com sucesso: {processed}/{total} feições processadas"
            elif self.language == MessageLanguage.SPANISH:
                return f"Exportación completada exitosamente: {processed}/{total} características procesadas"
            else:
                return f"Export completed successfully: {processed}/{total} features processed"
        else:
            message_data = self.catalog.get_message(
                "export_completed_with_warnings",
                self.language,
                warning_count=warnings,
                error_count=errors
            )
            return self._format_message_with_suggestions(message_data)


def detect_qgis_language() -> MessageLanguage:
    """
    Detect QGIS interface language and return corresponding MessageLanguage.
    
    Returns:
        MessageLanguage enum value based on QGIS locale
    """
    try:
        from qgis.core import QgsApplication
        
        # Get QGIS locale
        locale = QgsApplication.instance().locale()
        
        # Map common locale codes to our supported languages
        language_mapping = {
            'pt': MessageLanguage.PORTUGUESE,
            'pt_BR': MessageLanguage.PORTUGUESE,
            'pt_PT': MessageLanguage.PORTUGUESE,
            'es': MessageLanguage.SPANISH,
            'es_ES': MessageLanguage.SPANISH,
            'es_MX': MessageLanguage.SPANISH,
            'en': MessageLanguage.ENGLISH,
            'en_US': MessageLanguage.ENGLISH,
            'en_GB': MessageLanguage.ENGLISH,
        }
        
        # Try exact match first
        if locale in language_mapping:
            return language_mapping[locale]
        
        # Try language code only (first two characters)
        lang_code = locale[:2] if len(locale) >= 2 else locale
        if lang_code in language_mapping:
            return language_mapping[lang_code]
        
        # Default to English
        return MessageLanguage.ENGLISH
        
    except Exception:
        # If detection fails, default to English
        return MessageLanguage.ENGLISH


def create_error_formatter() -> UserFriendlyErrorFormatter:
    """
    Create error formatter with automatically detected language.
    
    Returns:
        UserFriendlyErrorFormatter configured for current QGIS language
    """
    detected_language = detect_qgis_language()
    return UserFriendlyErrorFormatter(detected_language)