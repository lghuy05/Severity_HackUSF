"use client";

import type { AnalyzeResponse, RiskLevel } from "@shared/types";

export type UiLanguage = "en" | "es" | "fr" | "pt" | "vi" | "zh";

export const LANGUAGE_OPTIONS: Array<{ value: UiLanguage; label: string; speech: string }> = [
  { value: "en", label: "English", speech: "en-US" },
  { value: "es", label: "Español", speech: "es-ES" },
  { value: "fr", label: "Français", speech: "fr-FR" },
  { value: "pt", label: "Português", speech: "pt-BR" },
  { value: "vi", label: "Tiếng Việt", speech: "vi-VN" },
  { value: "zh", label: "中文", speech: "zh-CN" },
];

type TranslationSet = {
  appBadge: string;
  headline: string;
  subtext: string;
  locationUsing: (value: string) => string;
  locationPrompt: string;
  voiceReady: string;
  voiceUnavailable: string;
  conversationTitle: string;
  reviewingTitle: string;
  promptPlaceholder: string;
  locationPlaceholder: string;
  continue: string;
  newChat: string;
  careAssistant: string;
  reviewing: string;
  understandingIntro: (text: string) => string;
    riskMessage: (risk: RiskLevel, explanation: string) => string;
  actionMessageHigh: string;
  actionMessageNormal: string;
  errorMessage: string;
  guidanceEyebrow: string;
  guidanceTitle: string;
  understandingLabel: string;
  recommendedActionLabel: string;
  nextStepsLabel: string;
  describedAs: (text: string) => string;
  actionHigh: string;
  actionNormal: (recommendation: string) => string;
  nextSteps: (analysis: AnalyzeResponse) => string[];
  careOptionsEyebrow: string;
  careOptionsTitle: string;
  careOptionsDescription: string;
  compareCosts: string;
  hideCosts: string;
  costRange: string;
  waitTime: string;
  coverage: string;
  call: string;
  directions: string;
  compare: string;
  openNow: string;
  hoursUnavailable: string;
  estimatedCostsReady: string;
  noCosts: string;
  urgentGuidance: string;
  urgentBody: string;
  viewEmergencyInstructions: string;
    callEmergency: string;
    systemView: string;
    emergencyInstructions: string[];
  };

function riskWord(language: UiLanguage, risk: RiskLevel) {
  const table: Record<UiLanguage, Record<RiskLevel, string>> = {
    en: { low: "low", medium: "medium", high: "high" },
    es: { low: "bajo", medium: "medio", high: "alto" },
    fr: { low: "faible", medium: "modéré", high: "élevé" },
    pt: { low: "baixo", medium: "médio", high: "alto" },
    vi: { low: "thấp", medium: "trung bình", high: "cao" },
    zh: { low: "低", medium: "中", high: "高" },
  };

  return table[language][risk];
}

export const UI_COPY: Record<UiLanguage, TranslationSet> = {
  en: {
    appBadge: "AI healthcare navigator",
    headline: "Clear guidance from symptoms to next steps.",
    subtext: "Describe what you are feeling once. We help translate the concern into plain language, assess urgency, and guide you toward the right kind of care nearby.",
    locationUsing: (value) => `Using location: ${value}`,
    locationPrompt: "Add your city, ZIP code, or current location",
    voiceReady: "Voice input available in this browser",
    voiceUnavailable: "Voice input depends on browser support",
    conversationTitle: "Conversation",
    reviewingTitle: "Reviewing your symptoms",
    promptPlaceholder: "Describe what you're feeling in your own words",
    locationPlaceholder: "Your city, ZIP code, or current location",
    continue: "Continue",
    newChat: "New chat",
    careAssistant: "Care assistant",
    reviewing: "Reviewing",
    understandingIntro: (text) => `I understand this as: ${text}.`,
    riskMessage: (risk) => `Based on your symptoms, this appears to be ${riskWord("en", risk)} risk right now.`,
    actionMessageHigh: "This may need urgent medical attention. Please use the emergency guidance and seek care right away.",
    actionMessageNormal: "I found the next step that fits your symptoms and location.",
    errorMessage: "I couldn't review your symptoms right now. Please try again in a moment. If this feels urgent, go to the nearest emergency department or call 911.",
    guidanceEyebrow: "Care guidance",
    guidanceTitle: "What to do next",
    understandingLabel: "Understanding",
    recommendedActionLabel: "Recommended action",
    nextStepsLabel: "Next steps",
    describedAs: (text) => `You described: ${text}`,
    actionHigh: "Seek urgent medical care now. If symptoms are getting worse or you feel unsafe, call emergency services immediately.",
    actionNormal: (recommendation) => recommendation || "Follow the care option below that best matches your symptoms and coverage.",
    nextSteps: (analysis) => {
      const steps: string[] = [];
      if (analysis.navigation.hospitals.length > 0) steps.push(`Nearby care options were found near ${analysis.navigation.origin}.`);
      if (analysis.cost_options.length > 0) steps.push("Estimated cost ranges are available if you want to compare options.");
      if (analysis.provider_message) steps.push("A provider-ready summary has been prepared so you do not need to repeat everything from scratch.");
      return steps;
    },
    careOptionsEyebrow: "Care options",
    careOptionsTitle: "Places you can contact next",
    careOptionsDescription: "These options are based on your location and the current guidance from the assistant.",
    compareCosts: "Compare costs",
    hideCosts: "Hide costs",
    costRange: "Cost range",
    waitTime: "Wait time",
    coverage: "Coverage",
    call: "Call",
    directions: "Directions",
    compare: "Compare",
    openNow: "Open now",
    hoursUnavailable: "Hours unavailable",
    estimatedCostsReady: "Estimated cost comparison",
    noCosts: "Cost details are not available for this option.",
    urgentGuidance: "Urgent guidance",
    urgentBody: "These symptoms may need urgent medical attention. If they are worsening or you feel unsafe, call 911 now or go to the nearest emergency department.",
    viewEmergencyInstructions: "View emergency instructions",
    callEmergency: "Call 911",
    systemView: "Agent Graph",
    emergencyInstructions: ["Call 911 immediately.", "Do not drive yourself.", "Stay with someone if possible."],
  },
  es: {
    appBadge: "Navegador de salud con IA",
    headline: "Orientación clara desde los síntomas hasta los próximos pasos.",
    subtext: "Describe lo que sientes una sola vez. Te ayudamos a entender la situación, evaluar la urgencia y encontrar la atención adecuada cerca de ti.",
    locationUsing: (value) => `Ubicación actual: ${value}`,
    locationPrompt: "Agrega tu ciudad, código postal o ubicación actual",
    voiceReady: "Entrada por voz disponible en este navegador",
    voiceUnavailable: "La voz depende de la compatibilidad del navegador",
    conversationTitle: "Conversación",
    reviewingTitle: "Revisando tus síntomas",
    promptPlaceholder: "Describe lo que sientes con tus propias palabras",
    locationPlaceholder: "Tu ciudad, código postal o ubicación actual",
    continue: "Continuar",
    newChat: "Nuevo chat",
    careAssistant: "Asistente de salud",
    reviewing: "Revisando",
    understandingIntro: (text) => `Entiendo esto como: ${text}.`,
    riskMessage: (risk) => `Según tus síntomas, esto parece de riesgo ${riskWord("es", risk)} en este momento.`,
    actionMessageHigh: "Esto puede requerir atención médica urgente. Usa la guía de emergencia y busca atención de inmediato.",
    actionMessageNormal: "Encontré el siguiente paso que mejor se ajusta a tus síntomas y ubicación.",
    errorMessage: "No pude revisar tus síntomas en este momento. Inténtalo de nuevo en un momento. Si esto parece urgente, ve al servicio de urgencias más cercano o llama al 911.",
    guidanceEyebrow: "Orientación",
    guidanceTitle: "Qué hacer ahora",
    understandingLabel: "Comprensión",
    recommendedActionLabel: "Acción recomendada",
    nextStepsLabel: "Siguientes pasos",
    describedAs: (text) => `Describiste: ${text}`,
    actionHigh: "Busca atención médica urgente ahora. Si los síntomas empeoran o te sientes en peligro, llama a emergencias de inmediato.",
    actionNormal: (recommendation) => recommendation || "Sigue la opción de atención que mejor se ajuste a tus síntomas y cobertura.",
    nextSteps: (analysis) => {
      const steps: string[] = [];
      if (analysis.navigation.hospitals.length > 0) steps.push(`Se encontraron opciones de atención cerca de ${analysis.navigation.origin}.`);
      if (analysis.cost_options.length > 0) steps.push("Hay rangos de costo estimados si quieres comparar opciones.");
      if (analysis.provider_message) steps.push("Se preparó un resumen para el proveedor para que no tengas que repetir todo desde cero.");
      return steps;
    },
    careOptionsEyebrow: "Opciones de atención",
    careOptionsTitle: "Lugares a los que puedes acudir ahora",
    careOptionsDescription: "Estas opciones se basan en tu ubicación y en la orientación actual del asistente.",
    compareCosts: "Comparar costos",
    hideCosts: "Ocultar costos",
    costRange: "Rango de costo",
    waitTime: "Tiempo de espera",
    coverage: "Cobertura",
    call: "Llamar",
    directions: "Cómo llegar",
    compare: "Comparar",
    openNow: "Abierto ahora",
    hoursUnavailable: "Horario no disponible",
    estimatedCostsReady: "Comparación estimada de costos",
    noCosts: "No hay detalles de costo disponibles para esta opción.",
    urgentGuidance: "Guía urgente",
    urgentBody: "Estos síntomas pueden necesitar atención médica urgente. Si empeoran o te sientes en peligro, llama al 911 ahora o ve al servicio de urgencias más cercano.",
    viewEmergencyInstructions: "Ver instrucciones de emergencia",
    callEmergency: "Llamar al 911",
    systemView: "Agent Graph",
    emergencyInstructions: ["Llama al 911 de inmediato.", "No conduzcas por tu cuenta.", "Permanece con alguien si es posible."],
  },
  fr: {
    appBadge: "Navigateur de santé IA",
    headline: "Des conseils clairs, des symptômes aux prochaines étapes.",
    subtext: "Décrivez ce que vous ressentez une seule fois. Nous clarifions la situation, évaluons l'urgence et vous guidons vers le bon type de soins près de chez vous.",
    locationUsing: (value) => `Position utilisée : ${value}`,
    locationPrompt: "Ajoutez votre ville, code postal ou position actuelle",
    voiceReady: "La saisie vocale est disponible dans ce navigateur",
    voiceUnavailable: "La voix dépend du support du navigateur",
    conversationTitle: "Conversation",
    reviewingTitle: "Analyse de vos symptômes",
    promptPlaceholder: "Décrivez ce que vous ressentez avec vos propres mots",
    locationPlaceholder: "Votre ville, code postal ou position actuelle",
    continue: "Continuer",
    newChat: "Nouveau chat",
    careAssistant: "Assistant santé",
    reviewing: "Analyse en cours",
    understandingIntro: (text) => `Je comprends cela comme : ${text}.`,
    riskMessage: (risk) => `D'après vos symptômes, cela semble être un niveau de risque ${riskWord("fr", risk)} pour le moment.`,
    actionMessageHigh: "Cela peut nécessiter une prise en charge urgente. Utilisez les consignes d'urgence et cherchez des soins immédiatement.",
    actionMessageNormal: "J'ai trouvé l'étape suivante adaptée à vos symptômes et à votre position.",
    errorMessage: "Je n'ai pas pu examiner vos symptômes pour le moment. Réessayez dans un instant. Si cela semble urgent, rendez-vous au service d'urgence le plus proche ou appelez le 911.",
    guidanceEyebrow: "Conseils",
    guidanceTitle: "Ce qu'il faut faire maintenant",
    understandingLabel: "Compréhension",
    recommendedActionLabel: "Action recommandée",
    nextStepsLabel: "Prochaines étapes",
    describedAs: (text) => `Vous avez décrit : ${text}`,
    actionHigh: "Cherchez des soins urgents maintenant. Si les symptômes s'aggravent ou si vous vous sentez en danger, appelez immédiatement les secours.",
    actionNormal: (recommendation) => recommendation || "Choisissez l'option de soins ci-dessous qui correspond le mieux à vos symptômes.",
    nextSteps: (analysis) => {
      const steps: string[] = [];
      if (analysis.navigation.hospitals.length > 0) steps.push(`Des options de soins ont été trouvées près de ${analysis.navigation.origin}.`);
      if (analysis.cost_options.length > 0) steps.push("Des fourchettes de coût estimées sont disponibles si vous souhaitez comparer.");
      if (analysis.provider_message) steps.push("Un résumé pour le professionnel de santé est prêt pour éviter de tout répéter.");
      return steps;
    },
    careOptionsEyebrow: "Options de soins",
    careOptionsTitle: "Lieux à contacter ensuite",
    careOptionsDescription: "Ces options sont basées sur votre position et sur l'orientation actuelle de l'assistant.",
    compareCosts: "Comparer les coûts",
    hideCosts: "Masquer les coûts",
    costRange: "Fourchette de coût",
    waitTime: "Temps d'attente",
    coverage: "Couverture",
    call: "Appeler",
    directions: "Itinéraire",
    compare: "Comparer",
    openNow: "Ouvert",
    hoursUnavailable: "Horaires indisponibles",
    estimatedCostsReady: "Comparaison estimée des coûts",
    noCosts: "Les détails de coût ne sont pas disponibles pour cette option.",
    urgentGuidance: "Conseils urgents",
    urgentBody: "Ces symptômes peuvent nécessiter une prise en charge urgente. S'ils s'aggravent ou si vous vous sentez en danger, appelez le 911 ou rendez-vous aux urgences les plus proches.",
    viewEmergencyInstructions: "Voir les consignes d'urgence",
    callEmergency: "Appeler le 911",
    systemView: "Agent Graph",
    emergencyInstructions: ["Appelez immédiatement le 911.", "Ne conduisez pas vous-même.", "Restez avec quelqu'un si possible."],
  },
  pt: {
    appBadge: "Navegador de saúde com IA",
    headline: "Orientação clara dos sintomas aos próximos passos.",
    subtext: "Descreva o que você está sentindo uma única vez. Ajudamos a entender a situação, avaliar a urgência e encontrar o cuidado certo perto de você.",
    locationUsing: (value) => `Local atual: ${value}`,
    locationPrompt: "Adicione sua cidade, CEP ou localização atual",
    voiceReady: "Entrada por voz disponível neste navegador",
    voiceUnavailable: "A voz depende do suporte do navegador",
    conversationTitle: "Conversa",
    reviewingTitle: "Analisando seus sintomas",
    promptPlaceholder: "Descreva o que você está sentindo com suas próprias palavras",
    locationPlaceholder: "Sua cidade, CEP ou localização atual",
    continue: "Continuar",
    newChat: "Nova conversa",
    careAssistant: "Assistente de saúde",
    reviewing: "Analisando",
    understandingIntro: (text) => `Entendo isso como: ${text}.`,
    riskMessage: (risk) => `Com base nos seus sintomas, isso parece ter risco ${riskWord("pt", risk)} neste momento.`,
    actionMessageHigh: "Isso pode exigir atendimento médico urgente. Use a orientação de emergência e procure atendimento imediatamente.",
    actionMessageNormal: "Encontrei o próximo passo que melhor se encaixa nos seus sintomas e na sua localização.",
    errorMessage: "Não consegui analisar seus sintomas agora. Tente novamente em instantes. Se isso parecer urgente, vá ao pronto-socorro mais próximo ou ligue para o 911.",
    guidanceEyebrow: "Orientação",
    guidanceTitle: "O que fazer agora",
    understandingLabel: "Entendimento",
    recommendedActionLabel: "Ação recomendada",
    nextStepsLabel: "Próximos passos",
    describedAs: (text) => `Você descreveu: ${text}`,
    actionHigh: "Procure atendimento médico urgente agora. Se os sintomas piorarem ou você se sentir em perigo, ligue para a emergência imediatamente.",
    actionNormal: (recommendation) => recommendation || "Siga a opção de cuidado abaixo que melhor combina com seus sintomas.",
    nextSteps: (analysis) => {
      const steps: string[] = [];
      if (analysis.navigation.hospitals.length > 0) steps.push(`Foram encontradas opções de atendimento perto de ${analysis.navigation.origin}.`);
      if (analysis.cost_options.length > 0) steps.push("Há faixas estimadas de custo caso você queira comparar opções.");
      if (analysis.provider_message) steps.push("Um resumo para o profissional de saúde foi preparado para evitar que você repita tudo do zero.");
      return steps;
    },
    careOptionsEyebrow: "Opções de cuidado",
    careOptionsTitle: "Lugares para procurar em seguida",
    careOptionsDescription: "Essas opções são baseadas na sua localização e na orientação atual do assistente.",
    compareCosts: "Comparar custos",
    hideCosts: "Ocultar custos",
    costRange: "Faixa de custo",
    waitTime: "Tempo de espera",
    coverage: "Cobertura",
    call: "Ligar",
    directions: "Direções",
    compare: "Comparar",
    openNow: "Aberto agora",
    hoursUnavailable: "Horário indisponível",
    estimatedCostsReady: "Comparação estimada de custos",
    noCosts: "Os detalhes de custo não estão disponíveis para esta opção.",
    urgentGuidance: "Orientação urgente",
    urgentBody: "Esses sintomas podem precisar de atendimento médico urgente. Se estiverem piorando ou você se sentir em perigo, ligue para o 911 agora ou vá ao pronto-socorro mais próximo.",
    viewEmergencyInstructions: "Ver instruções de emergência",
    callEmergency: "Ligar para 911",
    systemView: "Agent Graph",
    emergencyInstructions: ["Ligue para o 911 imediatamente.", "Não dirija por conta própria.", "Fique com alguém, se possível."],
  },
  vi: {
    appBadge: "Trợ lý điều hướng y tế AI",
    headline: "Hướng dẫn rõ ràng từ triệu chứng đến bước tiếp theo.",
    subtext: "Chỉ cần mô tả cảm giác của bạn một lần. Chúng tôi giúp diễn giải tình trạng, đánh giá mức độ khẩn cấp và hướng bạn đến nơi chăm sóc phù hợp gần bạn.",
    locationUsing: (value) => `Vị trí đang dùng: ${value}`,
    locationPrompt: "Thêm thành phố, mã ZIP hoặc vị trí hiện tại của bạn",
    voiceReady: "Nhập bằng giọng nói khả dụng trên trình duyệt này",
    voiceUnavailable: "Tính năng giọng nói phụ thuộc vào trình duyệt",
    conversationTitle: "Cuộc trò chuyện",
    reviewingTitle: "Đang xem xét triệu chứng của bạn",
    promptPlaceholder: "Mô tả cảm giác của bạn bằng lời của chính bạn",
    locationPlaceholder: "Thành phố, mã ZIP hoặc vị trí hiện tại của bạn",
    continue: "Tiếp tục",
    newChat: "Cuộc trò chuyện mới",
    careAssistant: "Trợ lý chăm sóc",
    reviewing: "Đang xem xét",
    understandingIntro: (text) => `Tôi hiểu tình trạng này là: ${text}.`,
    riskMessage: (risk) => `Dựa trên triệu chứng của bạn, hiện tại đây có vẻ là mức nguy cơ ${riskWord("vi", risk)}.`,
    actionMessageHigh: "Tình trạng này có thể cần được chăm sóc y tế khẩn cấp. Hãy dùng hướng dẫn khẩn cấp và đi khám ngay.",
    actionMessageNormal: "Tôi đã tìm được bước tiếp theo phù hợp với triệu chứng và vị trí của bạn.",
    errorMessage: "Tôi chưa thể đánh giá triệu chứng của bạn lúc này. Vui lòng thử lại sau ít phút. Nếu thấy khẩn cấp, hãy đến khoa cấp cứu gần nhất hoặc gọi 911.",
    guidanceEyebrow: "Hướng dẫn chăm sóc",
    guidanceTitle: "Bạn nên làm gì tiếp theo",
    understandingLabel: "Tóm tắt tình trạng",
    recommendedActionLabel: "Hành động được khuyến nghị",
    nextStepsLabel: "Các bước tiếp theo",
    describedAs: (text) => `Bạn đã mô tả: ${text}`,
    actionHigh: "Hãy đi cấp cứu ngay. Nếu triệu chứng nặng hơn hoặc bạn cảm thấy không an toàn, hãy gọi cấp cứu ngay lập tức.",
    actionNormal: (recommendation) => recommendation || "Hãy chọn phương án chăm sóc bên dưới phù hợp nhất với triệu chứng và bảo hiểm của bạn.",
    nextSteps: (analysis) => {
      const steps: string[] = [];
      if (analysis.navigation.hospitals.length > 0) steps.push(`Đã tìm thấy các cơ sở chăm sóc gần ${analysis.navigation.origin}.`);
      if (analysis.cost_options.length > 0) steps.push("Có sẵn khoảng chi phí ước tính nếu bạn muốn so sánh các lựa chọn.");
      if (analysis.provider_message) steps.push("Đã chuẩn bị sẵn bản tóm tắt cho cơ sở y tế để bạn không phải lặp lại mọi thứ từ đầu.");
      return steps;
    },
    careOptionsEyebrow: "Lựa chọn chăm sóc",
    careOptionsTitle: "Những nơi bạn có thể liên hệ tiếp theo",
    careOptionsDescription: "Các lựa chọn này dựa trên vị trí của bạn và hướng dẫn hiện tại từ trợ lý.",
    compareCosts: "So sánh chi phí",
    hideCosts: "Ẩn chi phí",
    costRange: "Khoảng chi phí",
    waitTime: "Thời gian chờ",
    coverage: "Bảo hiểm",
    call: "Gọi",
    directions: "Chỉ đường",
    compare: "So sánh",
    openNow: "Đang mở cửa",
    hoursUnavailable: "Chưa rõ giờ hoạt động",
    estimatedCostsReady: "So sánh chi phí ước tính",
    noCosts: "Chưa có thông tin chi phí cho lựa chọn này.",
    urgentGuidance: "Hướng dẫn khẩn cấp",
    urgentBody: "Những triệu chứng này có thể cần chăm sóc y tế khẩn cấp. Nếu đang nặng hơn hoặc bạn cảm thấy không an toàn, hãy gọi 911 ngay hoặc đến khoa cấp cứu gần nhất.",
    viewEmergencyInstructions: "Xem hướng dẫn khẩn cấp",
    callEmergency: "Gọi 911",
    systemView: "Agent Graph",
    emergencyInstructions: ["Gọi 911 ngay lập tức.", "Không tự lái xe.", "Nếu có thể, hãy ở cùng một người khác."],
  },
  zh: {
    appBadge: "AI 医疗导航助手",
    headline: "从症状到下一步，给你清晰指引。",
    subtext: "只需描述一次你的感受。我们会帮助你理解情况、评估紧急程度，并引导你找到附近合适的医疗资源。",
    locationUsing: (value) => `当前使用位置：${value}`,
    locationPrompt: "请输入你的城市、邮编或当前位置",
    voiceReady: "当前浏览器支持语音输入",
    voiceUnavailable: "语音功能取决于浏览器支持",
    conversationTitle: "对话",
    reviewingTitle: "正在分析你的症状",
    promptPlaceholder: "请用你自己的话描述你的感受",
    locationPlaceholder: "你的城市、邮编或当前位置",
    continue: "继续",
    newChat: "新对话",
    careAssistant: "医疗助手",
    reviewing: "正在分析",
    understandingIntro: (text) => `我理解你的情况是：${text}。`,
    riskMessage: (risk) => `根据你的症状，目前看起来属于${riskWord("zh", risk)}风险。`,
    actionMessageHigh: "这可能需要紧急医疗处理。请查看紧急指引并尽快就医。",
    actionMessageNormal: "我已经找到了适合你症状和位置的下一步建议。",
    errorMessage: "我现在无法完成症状分析。请稍后再试。如果情况紧急，请前往最近的急诊室或拨打 911。",
    guidanceEyebrow: "护理指引",
    guidanceTitle: "你现在该怎么做",
    understandingLabel: "情况理解",
    recommendedActionLabel: "建议行动",
    nextStepsLabel: "下一步",
    describedAs: (text) => `你描述的是：${text}`,
    actionHigh: "请立即寻求紧急医疗帮助。如果症状加重或你感觉不安全，请立刻拨打急救电话。",
    actionNormal: (recommendation) => recommendation || "请根据你的症状和保障情况，选择下面最合适的就医方式。",
    nextSteps: (analysis) => {
      const steps: string[] = [];
      if (analysis.navigation.hospitals.length > 0) steps.push(`已找到 ${analysis.navigation.origin} 附近的就医地点。`);
      if (analysis.cost_options.length > 0) steps.push("如果你想比较不同选择，可以查看预估费用范围。");
      if (analysis.provider_message) steps.push("已为你准备好可直接提供给医生的摘要，避免重复说明。");
      return steps;
    },
    careOptionsEyebrow: "就医选项",
    careOptionsTitle: "你现在可以联系的地点",
    careOptionsDescription: "这些选项基于你的位置以及当前的医疗建议。",
    compareCosts: "比较费用",
    hideCosts: "隐藏费用",
    costRange: "费用范围",
    waitTime: "等待时间",
    coverage: "保障情况",
    call: "拨打电话",
    directions: "路线导航",
    compare: "比较",
    openNow: "营业中",
    hoursUnavailable: "营业时间未知",
    estimatedCostsReady: "预估费用对比",
    noCosts: "此选项暂无费用信息。",
    urgentGuidance: "紧急指引",
    urgentBody: "这些症状可能需要紧急医疗处理。如果症状加重或你感觉不安全，请立即拨打 911 或前往最近的急诊室。",
    viewEmergencyInstructions: "查看紧急指引",
    callEmergency: "拨打 911",
    systemView: "Agent Graph",
    emergencyInstructions: ["请立即拨打 911。", "不要自行驾车。", "如果可以，请与他人待在一起。"],
  },
};

export function getUiCopy(language: UiLanguage) {
  return UI_COPY[language];
}

export function speechLocaleFor(language: UiLanguage) {
  return LANGUAGE_OPTIONS.find((option) => option.value === language)?.speech ?? "en-US";
}
