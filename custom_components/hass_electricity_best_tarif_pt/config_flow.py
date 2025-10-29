import voluptuous as vol
import logging
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from .const import DOMAIN, ENERGY_TYPE_OPTIONS
from .data_loader import async_get_comercializadores, async_get_tariff_details_for_comercializador

_LOGGER = logging.getLogger(__name__)

COND_COMERCIAIS_URL = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/csv%5CCondComerciais.csv"
PRECOS_ELEGN_URL = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/csv%5CPrecos_ELEGN.csv"

pot_cont_values = ["1,15", "2,3", "3,45", "4,6", "5,75", "6,9", "10,35", "13,8", "17,25", "20,7", "27,6", "34,5", "41,4"]  # Portuguese format with commas
codigo_oferta_list = ["COD_Proposta",
                    "TUR",
                    "CUR",
                    "U1",
                    "ACCIONA_02",
                    "ACCIONA_01",
                    "ALFAENERGIA_03",
                    "ALFAENERGIA_04",
                    "ALFAENERGIA_01",
                    "ALFAENERGIA_02",
                    "AUDAX_03",
                    "AUDAX_04",
                    "AUDAX_01",
                    "AUDAX_02",
                    "AXPO_03",
                    "AXPO_04",
                    "AXPO_01",
                    "AXPO_02",
                    "COOP_04",
                    "COOP_02",
                    "DOUROGAS_03",
                    "DOUROGAS_04",
                    "DOUROGAS_01",
                    "DOUROGAS_02",
                    "EDPC_86",
                    "EDPC_85",
                    "EDPC_88",
                    "EDPC_87",
                    "EDPC_82",
                    "EDPC_81",
                    "EDPC_84",
                    "EDPC_83",
                    "EDPC_130",
                    "EDPC_129",
                    "EDPC_132",
                    "EDPC_131",
                    "EDPC_126",
                    "EDPC_125",
                    "EDPC_128",
                    "EDPC_127",
                    "EDPC_133",
                    "EDPC_139",
                    "EDPC_138",
                    "EDPC_141",
                    "EDPC_140",
                    "EDPC_135",
                    "EDPC_134",
                    "EDPC_137",
                    "EDPC_136",
                    "EDPC_124",
                    "EDPC_112",
                    "EDPC_111",
                    "EDPC_114",
                    "EDPC_113",
                    "EDPC_108",
                    "EDPC_107",
                    "EDPC_110",
                    "EDPC_109",
                    "EDPC_115",
                    "EDPC_121",
                    "EDPC_120",
                    "EDPC_123",
                    "EDPC_122",
                    "EDPC_117",
                    "EDPC_116",
                    "EDPC_119",
                    "EDPC_118",
                    "EDPC_71",
                    "EDPC_24",
                    "EDPC_23",
                    "EDPC_26",
                    "EDPC_25",
                    "EDPC_20",
                    "EDPC_19",
                    "EDPC_22",
                    "EDPC_21",
                    "EDPC_27",
                    "EDPC_33",
                    "EDPC_32",
                    "EDPC_35",
                    "EDPC_34",
                    "EDPC_29",
                    "EDPC_28",
                    "EDPC_31",
                    "EDPC_30",
                    "EDPC_18",
                    "EDPC_06",
                    "EDPC_05",
                    "EDPC_08",
                    "EDPC_07",
                    "EDPC_02",
                    "EDPC_01",
                    "EDPC_04",
                    "EDPC_03",
                    "EDPC_09",
                    "EDPC_15",
                    "EDPC_14",
                    "EDPC_17",
                    "EDPC_16",
                    "EDPC_11",
                    "EDPC_10",
                    "EDPC_13",
                    "EDPC_12",
                    "EDPC_59",
                    "EDPC_58",
                    "EDPC_61",
                    "EDPC_60",
                    "EDPC_55",
                    "EDPC_54",
                    "EDPC_57",
                    "EDPC_56",
                    "EDPC_62",
                    "EDPC_68",
                    "EDPC_67",
                    "EDPC_70",
                    "EDPC_69",
                    "EDPC_64",
                    "EDPC_63",
                    "EDPC_66",
                    "EDPC_65",
                    "EDPC_53",
                    "EDPC_41",
                    "EDPC_40",
                    "EDPC_43",
                    "EDPC_42",
                    "EDPC_37",
                    "EDPC_36",
                    "EDPC_39",
                    "EDPC_38",
                    "EDPC_44",
                    "EDPC_50",
                    "EDPC_49",
                    "EDPC_52",
                    "EDPC_51",
                    "EDPC_46",
                    "EDPC_45",
                    "EDPC_48",
                    "EDPC_47",
                    "ELERGONE_01",
                    "END_65",
                    "END_61",
                    "END_62",
                    "END_66",
                    "END_71",
                    "END_67",
                    "END_68",
                    "END_60",
                    "END_52",
                    "END_53",
                    "END_51",
                    "END_49",
                    "END_50",
                    "END_54",
                    "END_58",
                    "END_59",
                    "END_57",
                    "END_55",
                    "END_56",
                    "END_72",
                    "END_88",
                    "END_89",
                    "END_87",
                    "END_85",
                    "END_86",
                    "END_90",
                    "END_94",
                    "END_95",
                    "END_93",
                    "END_91",
                    "END_92",
                    "END_84",
                    "END_76",
                    "END_77",
                    "END_75",
                    "END_73",
                    "END_74",
                    "END_78",
                    "END_82",
                    "END_83",
                    "END_81",
                    "END_79",
                    "END_80",
                    "END_48",
                    "END_16",
                    "END_17",
                    "END_15",
                    "END_13",
                    "END_14",
                    "END_18",
                    "END_22",
                    "END_23",
                    "END_21",
                    "END_19",
                    "END_20",
                    "END_12",
                    "END_04",
                    "END_05",
                    "END_03",
                    "END_01",
                    "END_02",
                    "END_06",
                    "END_10",
                    "END_11",
                    "END_09",
                    "END_07",
                    "END_08",
                    "END_24",
                    "END_40",
                    "END_41",
                    "END_39",
                    "END_37",
                    "END_38",
                    "END_42",
                    "END_46",
                    "END_47",
                    "END_45",
                    "END_43",
                    "END_44",
                    "END_36",
                    "END_28",
                    "END_29",
                    "END_27",
                    "END_25",
                    "END_26",
                    "END_30",
                    "END_34",
                    "END_35",
                    "END_33",
                    "END_31",
                    "END_32",
                    "ENIPLENITUDE_14",
                    "ENIPLENITUDE_15",
                    "ENIPLENITUDE_13",
                    "ENIPLENITUDE_11",
                    "ENIPLENITUDE_12",
                    "ENIPLENITUDE_19",
                    "ENIPLENITUDE_20",
                    "ENIPLENITUDE_18",
                    "ENIPLENITUDE_16",
                    "ENIPLENITUDE_17",
                    "ENIPLENITUDE_04",
                    "ENIPLENITUDE_05",
                    "ENIPLENITUDE_03",
                    "ENIPLENITUDE_01",
                    "ENIPLENITUDE_02",
                    "ENIPLENITUDE_09",
                    "ENIPLENITUDE_10",
                    "ENIPLENITUDE_08",
                    "ENIPLENITUDE_06",
                    "ENIPLENITUDE_07",
                    "EZUENERGIA_07",
                    "EZUENERGIA_06",
                    "EZUENERGIA_08",
                    "EZUENERGIA_10",
                    "EZUENERGIA_09",
                    "EZUENERGIA_02",
                    "EZUENERGIA_01",
                    "EZUENERGIA_03",
                    "EZUENERGIA_05",
                    "EZUENERGIA_04",
                    "G9ENERGY_04",
                    "G9ENERGY_05",
                    "G9ENERGY_01",
                    "G9ENERGY_02",
                    "GALP_84",
                    "GALP_85",
                    "GALP_82",
                    "GALP_79",
                    "GALP_80",
                    "GALP_81",
                    "GALP_86",
                    "GALP_91",
                    "GALP_92",
                    "GALP_93",
                    "GALP_90",
                    "GALP_87",
                    "GALP_88",
                    "GALP_89",
                    "GALP_78",
                    "GALP_67",
                    "GALP_68",
                    "GALP_69",
                    "GALP_66",
                    "GALP_63",
                    "GALP_64",
                    "GALP_65",
                    "GALP_70",
                    "GALP_75",
                    "GALP_76",
                    "GALP_77",
                    "GALP_74",
                    "GALP_71",
                    "GALP_72",
                    "GALP_73",
                    "GALP_114",
                    "GALP_115",
                    "GALP_116",
                    "GALP_113",
                    "GALP_110",
                    "GALP_111",
                    "GALP_112",
                    "GALP_117",
                    "GALP_122",
                    "GALP_123",
                    "GALP_124",
                    "GALP_121",
                    "GALP_118",
                    "GALP_119",
                    "GALP_120",
                    "GALP_109",
                    "GALP_98",
                    "GALP_99",
                    "GALP_100",
                    "GALP_97",
                    "GALP_94",
                    "GALP_95",
                    "GALP_96",
                    "GALP_101",
                    "GALP_106",
                    "GALP_107",
                    "GALP_108",
                    "GALP_105",
                    "GALP_102",
                    "GALP_103",
                    "GALP_104",
                    "GALP_21",
                    "GALP_22",
                    "GALP_23",
                    "GALP_20",
                    "GALP_17",
                    "GALP_18",
                    "GALP_19",
                    "GALP_24",
                    "GALP_29",
                    "GALP_30",
                    "GALP_31",
                    "GALP_28",
                    "GALP_25",
                    "GALP_26",
                    "GALP_27",
                    "GALP_16",
                    "GALP_05",
                    "GALP_06",
                    "GALP_07",
                    "GALP_04",
                    "GALP_01",
                    "GALP_02",
                    "GALP_03",
                    "GALP_08",
                    "GALP_13",
                    "GALP_14",
                    "GALP_15",
                    "GALP_12",
                    "GALP_09",
                    "GALP_10",
                    "GALP_11",
                    "GALP_52",
                    "GALP_53",
                    "GALP_54",
                    "GALP_51",
                    "GALP_48",
                    "GALP_49",
                    "GALP_50",
                    "GALP_55",
                    "GALP_60",
                    "GALP_61",
                    "GALP_62",
                    "GALP_59",
                    "GALP_56",
                    "GALP_57",
                    "GALP_58",
                    "GALP_47",
                    "GALP_36",
                    "GALP_37",
                    "GALP_38",
                    "GALP_35",
                    "GALP_32",
                    "GALP_33",
                    "GALP_34",
                    "GALP_39",
                    "GALP_44",
                    "GALP_45",
                    "GALP_46",
                    "GALP_43",
                    "GALP_40",
                    "GALP_41",
                    "GALP_42",
                    "GOLD_31",
                    "GOLD_30",
                    "GOLD_32",
                    "GOLD_34",
                    "GOLD_33",
                    "GOLD_29",
                    "GOLD_25",
                    "GOLD_24",
                    "GOLD_26",
                    "GOLD_28",
                    "GOLD_27",
                    "GOLD_42",
                    "GOLD_41",
                    "GOLD_43",
                    "GOLD_45",
                    "GOLD_44",
                    "GOLD_40",
                    "GOLD_36",
                    "GOLD_35",
                    "GOLD_37",
                    "GOLD_39",
                    "GOLD_38",
                    "GOLD_23",
                    "GOLD_08",
                    "GOLD_07",
                    "GOLD_09",
                    "GOLD_11",
                    "GOLD_10",
                    "GOLD_06",
                    "GOLD_02",
                    "GOLD_01",
                    "GOLD_03",
                    "GOLD_05",
                    "GOLD_18",
                    "GOLD_20",
                    "GOLD_22",
                    "GOLD_21",
                    "GOLD_17",
                    "GOLD_13",
                    "GOLD_12",
                    "GOLD_14",
                    "GOLD_16",
                    "GOLD_15",
                    "IBD_38",
                    "IBD_37",
                    "IBD_36",
                    "IBD_39",
                    "IBD_42",
                    "IBD_41",
                    "IBD_40",
                    "IBD_31",
                    "IBD_30",
                    "IBD_29",
                    "IBD_32",
                    "IBD_35",
                    "IBD_34",
                    "IBD_33",
                    "IBD_52",
                    "IBD_51",
                    "IBD_50",
                    "IBD_53",
                    "IBD_56",
                    "IBD_55",
                    "IBD_54",
                    "IBD_45",
                    "IBD_44",
                    "IBD_43",
                    "IBD_46",
                    "IBD_49",
                    "IBD_48",
                    "IBD_47",
                    "IBD_10",
                    "IBD_09",
                    "IBD_08",
                    "IBD_11",
                    "IBD_14",
                    "IBD_13",
                    "IBD_12",
                    "IBD_03",
                    "IBD_02",
                    "IBD_01",
                    "IBD_04",
                    "IBD_07",
                    "IBD_06",
                    "IBD_05",
                    "IBD_24",
                    "IBD_23",
                    "IBD_22",
                    "IBD_25",
                    "IBD_28",
                    "IBD_27",
                    "IBD_26",
                    "IBD_17",
                    "IBD_16",
                    "IBD_15",
                    "IBD_18",
                    "IBD_20",
                    "IBD_19",
                    "IBELECTRA_07",
                    "IBELECTRA_06",
                    "IBELECTRA_08",
                    "IBELECTRA_10",
                    "IBELECTRA_09",
                    "IBELECTRA_02",
                    "IBELECTRA_01",
                    "IBELECTRA_03",
                    "IBELECTRA_05",
                    "IBELECTRA_04",
                    "JAFPLUS_02",
                    "JAFPLUS_01",
                    "LUZBOA_03",
                    "LUZBOA_04",
                    "LUZBOA_01",
                    "LUZBOA_02",
                    "LUZIGAS_03",
                    "LUZIGAS_04",
                    "LUZIGAS_01",
                    "LUZIGAS_02",
                    "MEOENERGIA_03",
                    "MEOENERGIA_02",
                    "MOEVE_01",
                    "MUON_03",
                    "MUON_04",
                    "MUON_01",
                    "MUON_02",
                    "NABALIAENERGIA_07",
                    "NABALIAENERGIA_06",
                    "NABALIAENERGIA_09",
                    "NABALIAENERGIA_08",
                    "NABALIAENERGIA_05",
                    "NABALIAENERGIA_02",
                    "NABALIAENERGIA_01",
                    "NABALIAENERGIA_04",
                    "NABALIAENERGIA_03",
                    "NOSSAENERGIA_03",
                    "NOSSAENERGIA_02",
                    "NOSSAENERGIA_01",
                    "OENEO_02",
                    "OENEO_01",
                    "PORTULOGOS_02",
                    "PORTULOGOS_01",
                    "REPSOL_103",
                    "REPSOL_102",
                    "REPSOL_105",
                    "REPSOL_104",
                    "REPSOL_101",
                    "REPSOL_98",
                    "REPSOL_97",
                    "REPSOL_100",
                    "REPSOL_99",
                    "REPSOL_106",
                    "REPSOL_113",
                    "REPSOL_112",
                    "REPSOL_115",
                    "REPSOL_114",
                    "REPSOL_111",
                    "REPSOL_108",
                    "REPSOL_107",
                    "REPSOL_110",
                    "REPSOL_109",
                    "REPSOL_84",
                    "REPSOL_83",
                    "REPSOL_86",
                    "REPSOL_85",
                    "REPSOL_82",
                    "REPSOL_79",
                    "REPSOL_78",
                    "REPSOL_81",
                    "REPSOL_80",
                    "REPSOL_87",
                    "REPSOL_94",
                    "REPSOL_93",
                    "REPSOL_96",
                    "REPSOL_95",
                    "REPSOL_92",
                    "REPSOL_89",
                    "REPSOL_88",
                    "REPSOL_91",
                    "REPSOL_90",
                    "REPSOL_116",
                    "REPSOL_142",
                    "REPSOL_141",
                    "REPSOL_144",
                    "REPSOL_143",
                    "REPSOL_140",
                    "REPSOL_137",
                    "REPSOL_136",
                    "REPSOL_139",
                    "REPSOL_138",
                    "REPSOL_145",
                    "REPSOL_152",
                    "REPSOL_151",
                    "REPSOL_154",
                    "REPSOL_153",
                    "REPSOL_150",
                    "REPSOL_147",
                    "REPSOL_146",
                    "REPSOL_149",
                    "REPSOL_148",
                    "REPSOL_123",
                    "REPSOL_122",
                    "REPSOL_125",
                    "REPSOL_124",
                    "REPSOL_121",
                    "REPSOL_118",
                    "REPSOL_117",
                    "REPSOL_120",
                    "REPSOL_119",
                    "REPSOL_126",
                    "REPSOL_133",
                    "REPSOL_132",
                    "REPSOL_135",
                    "REPSOL_134",
                    "REPSOL_131",
                    "REPSOL_128",
                    "REPSOL_127",
                    "REPSOL_130",
                    "REPSOL_129",
                    "REPSOL_26",
                    "REPSOL_25",
                    "REPSOL_28",
                    "REPSOL_27",
                    "REPSOL_24",
                    "REPSOL_21",
                    "REPSOL_20",
                    "REPSOL_23",
                    "REPSOL_22",
                    "REPSOL_29",
                    "REPSOL_36",
                    "REPSOL_35",
                    "REPSOL_38",
                    "REPSOL_37",
                    "REPSOL_34",
                    "REPSOL_31",
                    "REPSOL_30",
                    "REPSOL_33",
                    "REPSOL_32",
                    "REPSOL_07",
                    "REPSOL_06",
                    "REPSOL_09",
                    "REPSOL_08",
                    "REPSOL_05",
                    "REPSOL_02",
                    "REPSOL_01",
                    "REPSOL_04",
                    "REPSOL_03",
                    "REPSOL_10",
                    "REPSOL_17",
                    "REPSOL_16",
                    "REPSOL_19",
                    "REPSOL_18",
                    "REPSOL_15",
                    "REPSOL_12",
                    "REPSOL_11",
                    "REPSOL_14",
                    "REPSOL_13",
                    "REPSOL_39",
                    "REPSOL_65",
                    "REPSOL_64",
                    "REPSOL_67",
                    "REPSOL_66",
                    "REPSOL_63",
                    "REPSOL_60",
                    "REPSOL_59",
                    "REPSOL_62",
                    "REPSOL_61",
                    "REPSOL_68",
                    "REPSOL_75",
                    "REPSOL_74",
                    "REPSOL_77",
                    "REPSOL_76",
                    "REPSOL_73",
                    "REPSOL_70",
                    "REPSOL_69",
                    "REPSOL_72",
                    "REPSOL_71",
                    "REPSOL_46",
                    "REPSOL_45",
                    "REPSOL_48",
                    "REPSOL_47",
                    "REPSOL_44",
                    "REPSOL_41",
                    "REPSOL_40",
                    "REPSOL_43",
                    "REPSOL_42",
                    "REPSOL_49",
                    "REPSOL_56",
                    "REPSOL_55",
                    "REPSOL_58",
                    "REPSOL_57",
                    "REPSOL_54",
                    "REPSOL_51",
                    "REPSOL_50",
                    "REPSOL_53",
                    "REPSOL_52",
                    "SUNCORE_01",
                    "USENERGY_01",
                    "YESENERGY_02",
                    "YESENERGY_01",
                    "ZUG POWER_03",
                    "ZUG POWER_02",
                    "ZUG POWER_01"]

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tarifários Eletricidade PT."""

    VERSION = 2  # Increment version for new features

    def __init__(self):
        """Initialize config flow."""
        self._comercializadores = []
        self._selected_comercializador = None
        self._selected_energy_type = None
        self._available_tariffs = {}  # Changed from offer_codes to tariffs (code -> display_name)
        self._energy_sensors = []

    async def async_step_user(self, user_input=None):
        """Handle the initial step - select energy type and comercializador."""
        errors = {}
        
        if not self._comercializadores:
            try:
                self._comercializadores = await async_get_comercializadores(self.hass)
                if not self._comercializadores:
                    errors["base"] = "no_data"
            except Exception:
                errors["base"] = "cannot_connect"

        if user_input is not None:
            self._selected_comercializador = user_input["comercializador"]
            self._selected_energy_type = user_input["energy_type"]
            
            # If user wants consumption analysis, go to consumption config step
            if user_input.get("enable_consumption_analysis", False):
                return await self.async_step_consumption_config()
            else:
                return await self.async_step_config()

        if errors.get("base"):
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({}),
                errors=errors,
            )

        schema = vol.Schema({
            vol.Required("comercializador"): vol.In(self._comercializadores),
            vol.Required("energy_type", default="ele"): vol.In(ENERGY_TYPE_OPTIONS),
            vol.Optional("enable_consumption_analysis", default=False): bool,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "consumption_info": "Enable consumption analysis to get personalized tariff recommendations based on your actual energy usage patterns."
            }
        )

    async def async_step_consumption_config(self, user_input=None):
        """Handle consumption analysis configuration."""
        errors = {}
        
        # Load tariff details for current tariff selection if not already loaded
        if not self._available_tariffs and self._selected_comercializador and self._selected_energy_type:
            try:
                self._available_tariffs = await async_get_tariff_details_for_comercializador(
                    self.hass, self._selected_comercializador, self._selected_energy_type
                )
            except Exception as e:
                _LOGGER.error("Error fetching tariffs for consumption config: %s", e)
        
        # Get available energy sensors if not already loaded
        if not self._energy_sensors:
            try:
                entity_registry = async_get_entity_registry(self.hass)
                energy_sensors = []
                
                for entity in entity_registry.entities.values():
                    # Look for energy sensors (cumulative kWh)
                    if (entity.device_class == "energy" or 
                        "energy" in entity.entity_id.lower() or
                        "kwh" in entity.entity_id.lower() or
                        entity.unit_of_measurement in ["kWh", "Wh"]):
                        
                        state = self.hass.states.get(entity.entity_id)
                        if state and state.state not in ["unknown", "unavailable"]:
                            friendly_name = state.attributes.get("friendly_name", entity.entity_id)
                            energy_sensors.append({
                                "entity_id": entity.entity_id,
                                "name": f"{friendly_name} ({entity.entity_id})"
                            })
                
                self._energy_sensors = energy_sensors
                _LOGGER.debug("Found %d energy sensors", len(self._energy_sensors))
                
            except Exception as e:
                _LOGGER.error("Error loading energy sensors: %s", e)
                errors["base"] = "sensor_discovery_failed"

        if user_input is not None:
            return await self.async_step_config(consumption_config=user_input)

        if not self._energy_sensors:
            errors["base"] = "no_energy_sensors"
        
        # Create sensor selection options
        sensor_options = {sensor["entity_id"]: sensor["name"] for sensor in self._energy_sensors}
        
        # Create current tariff selection options
        tariff_options = {}
        if self._available_tariffs:
            tariff_options = {code: display_name for code, display_name in self._available_tariffs.items()}
        
        schema = vol.Schema({
            vol.Required("energy_sensor"): vol.In(sensor_options),
            vol.Optional("analysis_days", default=30): vol.All(int, vol.Range(min=7, max=365)),
            vol.Optional("tariff_type", default="bi_hourly"): vol.In({
                "bi_hourly": "Bi-horário (Ponta/Vazio)",
                "tri_hourly": "Tri-horário (Ponta/Cheias/Vazio)"
            }),
            vol.Optional("current_tariff_code"): vol.In(tariff_options) if tariff_options else str,
        })

        return self.async_show_form(
            step_id="consumption_config",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "comercializador": self._selected_comercializador,
                "energy_type": ENERGY_TYPE_OPTIONS[self._selected_energy_type],
                "tariff_count": len(self._available_tariffs) if self._available_tariffs else 0
            }
        )

    async def async_step_config(self, user_input=None, consumption_config=None):
        """Handle the configuration step - select power and codes."""
        errors = {}
        
        # Fetch tariff details for the selected comercializador and energy type if not already done
        if not self._available_tariffs and self._selected_comercializador and self._selected_energy_type:
            try:
                self._available_tariffs = await async_get_tariff_details_for_comercializador(
                    self.hass, self._selected_comercializador, self._selected_energy_type
                )
                if not self._available_tariffs:
                    _LOGGER.warning("No tariffs found for %s (%s)", self._selected_comercializador, self._selected_energy_type)
                    self._available_tariffs = {}
            except Exception as e:
                _LOGGER.error("Error fetching tariffs for %s (%s): %s", self._selected_comercializador, self._selected_energy_type, e)
                errors["base"] = "cannot_connect"

        if user_input is not None:
            # Create unique entry ID based on comercializador and timestamp
            unique_id = f"{self._selected_comercializador}_{int(self.hass.loop.time())}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Convert display names back to codes for codigos_oferta
            selected_codes = user_input.get("codigos_oferta", [])
            if self._available_tariffs and selected_codes:
                # Map display names back to codes
                display_to_code = {display_name: code for code, display_name in self._available_tariffs.items()}
                selected_codes = [display_to_code.get(item, item) for item in selected_codes]

            # Combine basic config with consumption config
            config_data = {
                "comercializador": self._selected_comercializador,
                "pot_cont": user_input.get("pot_cont"),
                "codigos_oferta": selected_codes,
                "energy_type": self._selected_energy_type
            }
            
            # Add consumption analysis config if provided
            if consumption_config:
                config_data.update({
                    "enable_consumption_analysis": True,
                    "energy_sensor": consumption_config["energy_sensor"],
                    "analysis_days": consumption_config.get("analysis_days", 30),
                    "tariff_type": consumption_config.get("tariff_type", "bi_hourly"),
                    "current_tariff_code": consumption_config.get("current_tariff_code"),
                })
            else:
                config_data["enable_consumption_analysis"] = False

            title = f"{self._selected_comercializador} ({ENERGY_TYPE_OPTIONS[self._selected_energy_type]})"
            if consumption_config:
                title += " - Smart Analysis"

            return self.async_create_entry(
                title=title,
                data=config_data,
            )

        # Create schema with available tariffs for this comercializador
        schema_dict = {
            vol.Required("pot_cont", default=pot_cont_values[0]): vol.In(pot_cont_values),
        }
        
        # Only add codigos_oferta if we have tariffs available
        if self._available_tariffs:
            # Create reversed mapping for display (display_name -> code)
            tariff_display_options = {display_name: code for code, display_name in self._available_tariffs.items()}
            schema_dict[vol.Optional("codigos_oferta", default=[])] = cv.multi_select(tariff_display_options)
        
        schema = vol.Schema(schema_dict)

        description_placeholders = {
            "comercializador": self._selected_comercializador,
            "energy_type": ENERGY_TYPE_OPTIONS[self._selected_energy_type]
        }
        
        if consumption_config:
            description_placeholders["consumption_sensor"] = consumption_config["energy_sensor"]
            description_placeholders["analysis_info"] = f"Analysis: {consumption_config['analysis_days']} days, {consumption_config['tariff_type']}"

        return self.async_show_form(
            step_id="config",
            data_schema=schema,
            description_placeholders=description_placeholders,
            errors=errors,
        )