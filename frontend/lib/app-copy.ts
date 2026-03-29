"use client";

import type { UiLanguage } from "@/lib/i18n";

type AppCopy = {
  nav: {
    tagline: string;
    home: string;
    visitAssistant: string;
    appointments: string;
    notes: string;
    agentGraph: string;
    profile: string;
  };
  appointments: {
    badge: string;
    title: string;
    description: string;
    loading: string;
    empty: string;
    confirmed: string;
    listenToRecording: string;
    reasonForVisit: string;
    instructions: string;
    doctor: string;
    location: string;
  };
  profile: {
    badge: string;
    title: string;
    description: string;
    defaultsTitle: string;
    defaultsDescription: string;
    statusLoading: string;
    statusSaved: string;
    statusEditing: string;
    name: string;
    preferredLanguage: string;
    defaultLocation: string;
    age: string;
    gender: string;
    saveProfile: string;
    saving: string;
    contextTitle: string;
    contextDescription: string;
    notSet: string;
  };
  records: {
    badge: string;
    title: string;
    description: string;
    loading: string;
    noNotesTitle: string;
    noNotesDescription: string;
    nothingSaved: string;
    nothingSavedDescription: string;
    openVisitAssistant: string;
    severity: string;
    expand: string;
    collapse: string;
  };
  graph: {
    emptyTitle: string;
    emptyDescription: string;
    emptyCta: string;
    eyebrow: string;
    title: string;
    description: string;
    panelTitle: string;
    panelDescription: string;
    input: string;
    semantic: string;
    decision: string;
    agent: string;
    output: string;
  };
  visit: {
    visitSummary: string;
    liveTranslator: string;
  };
};

const APP_COPY: Partial<Record<UiLanguage, AppCopy>> = {
  en: {
    nav: { tagline: "Guided care navigation", home: "Home", visitAssistant: "Visit assistant", appointments: "Appointments", notes: "Notes", agentGraph: "Agent Graph", profile: "Profile" },
    appointments: {
      badge: "Appointments", title: "Scheduled appointments", description: "Confirmed appointments for this user, ordered by the most recent scheduling activity.",
      loading: "Loading appointments...", empty: "No appointments scheduled yet", confirmed: "Confirmed", listenToRecording: "Listen to Recording",
      reasonForVisit: "Reason for visit", instructions: "Instructions", doctor: "Doctor", location: "Location",
    },
    profile: {
      badge: "Profile", title: "Personal settings", description: "These details are stored to your user profile and cached locally for faster future conversations.",
      defaultsTitle: "Assistant defaults", defaultsDescription: "Language and location are applied automatically to every new request.",
      statusLoading: "Loading", statusSaved: "Saved", statusEditing: "Editing", name: "Name", preferredLanguage: "Preferred language",
      defaultLocation: "Default location", age: "Age (optional)", gender: "Gender (optional)", saveProfile: "Save profile", saving: "Saving...",
      contextTitle: "Assistant context", contextDescription: "This profile is applied automatically before the assistant decides what to ask or do next.", notSet: "Not set",
    },
    records: {
      badge: "Saved Notes", title: "Doctor visit notes", description: "Saved AI-generated appointment notes for this user. Expand any card to read the full note.",
      loading: "Loading saved notes...", noNotesTitle: "No notes yet", noNotesDescription: "Generate a visit summary and save it to start building your note history.",
      nothingSaved: "Nothing saved yet", nothingSavedDescription: "Create an AI visit summary from the visit assistant and save it with a title. It will appear here automatically.",
      openVisitAssistant: "Open visit assistant", severity: "Severity", expand: "Expand", collapse: "Collapse",
    },
    graph: {
      emptyTitle: "No graph data yet", emptyDescription: "Run a symptom check from the main experience first. The agent graph will appear here once the backend returns an execution trace.",
      emptyCta: "Go to main experience", eyebrow: "System graph", title: "Agent Graph",
      description: "This graph visualizes semantic understanding, branching decisions, agent specialization, and tool usage from the existing frontend trace.",
      panelTitle: "Dynamic reasoning graph", panelDescription: "Judges can pan, zoom, and inspect each branch to see which specialist agent contributed and which tools were invoked.",
      input: "Input", semantic: "Semantic", decision: "Decision", agent: "Agent", output: "Output",
    },
    visit: { visitSummary: "Visit Summary", liveTranslator: "Live Translator" },
  },
  es: {
    nav: { tagline: "Navegación guiada de atención", home: "Inicio", visitAssistant: "Asistente de visita", appointments: "Citas", notes: "Notas", agentGraph: "Grafo de agentes", profile: "Perfil" },
    appointments: {
      badge: "Citas", title: "Citas programadas", description: "Citas confirmadas para este usuario, ordenadas por la programación más reciente.",
      loading: "Cargando citas...", empty: "Aún no hay citas programadas", confirmed: "Confirmada", listenToRecording: "Escuchar grabación",
      reasonForVisit: "Motivo de la visita", instructions: "Instrucciones", doctor: "Doctor", location: "Ubicación",
    },
    profile: {
      badge: "Perfil", title: "Configuración personal", description: "Estos datos se guardan en tu perfil y se almacenan localmente para acelerar conversaciones futuras.",
      defaultsTitle: "Valores del asistente", defaultsDescription: "El idioma y la ubicación se aplican automáticamente a cada nueva solicitud.",
      statusLoading: "Cargando", statusSaved: "Guardado", statusEditing: "Editando", name: "Nombre", preferredLanguage: "Idioma preferido",
      defaultLocation: "Ubicación predeterminada", age: "Edad (opcional)", gender: "Género (opcional)", saveProfile: "Guardar perfil", saving: "Guardando...",
      contextTitle: "Contexto del asistente", contextDescription: "Este perfil se aplica automáticamente antes de que el asistente decida qué preguntar o hacer.", notSet: "Sin definir",
    },
    records: {
      badge: "Notas guardadas", title: "Notas de la visita médica", description: "Notas de citas guardadas para este usuario. Expande cualquier tarjeta para leerla completa.",
      loading: "Cargando notas guardadas...", noNotesTitle: "Aún no hay notas", noNotesDescription: "Genera un resumen de visita y guárdalo para comenzar tu historial.",
      nothingSaved: "Todavía no hay nada guardado", nothingSavedDescription: "Crea un resumen de visita con IA y guárdalo con un título. Aparecerá aquí automáticamente.",
      openVisitAssistant: "Abrir asistente de visita", severity: "Severidad", expand: "Expandir", collapse: "Ocultar",
    },
    graph: {
      emptyTitle: "Aún no hay datos del grafo", emptyDescription: "Ejecuta primero una revisión de síntomas en la experiencia principal. El grafo aparecerá aquí cuando el backend devuelva la traza.",
      emptyCta: "Ir a la experiencia principal", eyebrow: "Grafo del sistema", title: "Grafo de agentes",
      description: "Este grafo visualiza comprensión semántica, decisiones, especialización de agentes y uso de herramientas a partir de la traza del frontend.",
      panelTitle: "Grafo dinámico de razonamiento", panelDescription: "Los jueces pueden mover, hacer zoom e inspeccionar cada rama para ver qué agente especializado contribuyó y qué herramientas se usaron.",
      input: "Entrada", semantic: "Semántica", decision: "Decisión", agent: "Agente", output: "Salida",
    },
    visit: { visitSummary: "Resumen de visita", liveTranslator: "Traductor en vivo" },
  },
  fr: {
    nav: { tagline: "Navigation guidée des soins", home: "Accueil", visitAssistant: "Assistant de visite", appointments: "Rendez-vous", notes: "Notes", agentGraph: "Graphe d'agents", profile: "Profil" },
    appointments: {
      badge: "Rendez-vous", title: "Rendez-vous programmés", description: "Rendez-vous confirmés pour cet utilisateur, triés par activité de planification la plus récente.",
      loading: "Chargement des rendez-vous...", empty: "Aucun rendez-vous programmé", confirmed: "Confirmé", listenToRecording: "Écouter l'enregistrement",
      reasonForVisit: "Motif de visite", instructions: "Instructions", doctor: "Médecin", location: "Lieu",
    },
    profile: {
      badge: "Profil", title: "Paramètres personnels", description: "Ces informations sont enregistrées dans votre profil et mises en cache localement pour accélérer les prochaines conversations.",
      defaultsTitle: "Paramètres de l'assistant", defaultsDescription: "La langue et la localisation sont appliquées automatiquement à chaque nouvelle demande.",
      statusLoading: "Chargement", statusSaved: "Enregistré", statusEditing: "Modification", name: "Nom", preferredLanguage: "Langue préférée",
      defaultLocation: "Localisation par défaut", age: "Âge (optionnel)", gender: "Genre (optionnel)", saveProfile: "Enregistrer le profil", saving: "Enregistrement...",
      contextTitle: "Contexte de l'assistant", contextDescription: "Ce profil est appliqué automatiquement avant que l'assistant décide quoi demander ou faire ensuite.", notSet: "Non défini",
    },
    records: {
      badge: "Notes enregistrées", title: "Notes de visite médicale", description: "Notes de rendez-vous enregistrées pour cet utilisateur. Développez une carte pour la lire en entier.",
      loading: "Chargement des notes...", noNotesTitle: "Aucune note", noNotesDescription: "Générez un résumé de visite et enregistrez-le pour commencer votre historique.",
      nothingSaved: "Rien n'est encore enregistré", nothingSavedDescription: "Créez un résumé de visite IA et enregistrez-le avec un titre. Il apparaîtra ici automatiquement.",
      openVisitAssistant: "Ouvrir l'assistant de visite", severity: "Gravité", expand: "Développer", collapse: "Réduire",
    },
    graph: {
      emptyTitle: "Aucune donnée de graphe", emptyDescription: "Lancez d'abord une vérification des symptômes depuis l'expérience principale. Le graphe apparaîtra ici une fois la trace renvoyée par le backend.",
      emptyCta: "Aller à l'expérience principale", eyebrow: "Graphe système", title: "Graphe d'agents",
      description: "Ce graphe visualise la compréhension sémantique, les décisions, la spécialisation des agents et l'usage des outils à partir de la trace frontend.",
      panelTitle: "Graphe dynamique de raisonnement", panelDescription: "Le jury peut déplacer, zoomer et inspecter chaque branche pour voir quel agent spécialisé a contribué et quels outils ont été invoqués.",
      input: "Entrée", semantic: "Sémantique", decision: "Décision", agent: "Agent", output: "Sortie",
    },
    visit: { visitSummary: "Résumé de visite", liveTranslator: "Traducteur en direct" },
  },
  pt: {
    nav: { tagline: "Navegação guiada de cuidados", home: "Início", visitAssistant: "Assistente de visita", appointments: "Consultas", notes: "Notas", agentGraph: "Grafo de agentes", profile: "Perfil" },
    appointments: {
      badge: "Consultas", title: "Consultas agendadas", description: "Consultas confirmadas para este usuário, ordenadas pela atividade de agendamento mais recente.",
      loading: "Carregando consultas...", empty: "Nenhuma consulta agendada ainda", confirmed: "Confirmada", listenToRecording: "Ouvir gravação",
      reasonForVisit: "Motivo da consulta", instructions: "Instruções", doctor: "Médico", location: "Local",
    },
    profile: {
      badge: "Perfil", title: "Configurações pessoais", description: "Esses dados são salvos no seu perfil e armazenados localmente para acelerar futuras conversas.",
      defaultsTitle: "Padrões do assistente", defaultsDescription: "Idioma e localização são aplicados automaticamente a cada nova solicitação.",
      statusLoading: "Carregando", statusSaved: "Salvo", statusEditing: "Editando", name: "Nome", preferredLanguage: "Idioma preferido",
      defaultLocation: "Localização padrão", age: "Idade (opcional)", gender: "Gênero (opcional)", saveProfile: "Salvar perfil", saving: "Salvando...",
      contextTitle: "Contexto do assistente", contextDescription: "Este perfil é aplicado automaticamente antes do assistente decidir o que perguntar ou fazer em seguida.", notSet: "Não definido",
    },
    records: {
      badge: "Notas salvas", title: "Notas da consulta", description: "Notas de consulta salvas para este usuário. Expanda qualquer cartão para ler a nota completa.",
      loading: "Carregando notas salvas...", noNotesTitle: "Ainda não há notas", noNotesDescription: "Gere um resumo da visita e salve-o para começar seu histórico.",
      nothingSaved: "Nada salvo ainda", nothingSavedDescription: "Crie um resumo de visita com IA e salve com um título. Ele aparecerá aqui automaticamente.",
      openVisitAssistant: "Abrir assistente de visita", severity: "Severidade", expand: "Expandir", collapse: "Recolher",
    },
    graph: {
      emptyTitle: "Ainda não há dados do grafo", emptyDescription: "Execute primeiro uma checagem de sintomas na experiência principal. O grafo aparecerá aqui quando o backend retornar um rastreamento.",
      emptyCta: "Ir para a experiência principal", eyebrow: "Grafo do sistema", title: "Grafo de agentes",
      description: "Este grafo visualiza entendimento semântico, decisões, especialização de agentes e uso de ferramentas a partir do rastreamento existente no frontend.",
      panelTitle: "Grafo dinâmico de raciocínio", panelDescription: "Os jurados podem mover, ampliar e inspecionar cada ramo para ver qual agente especializado contribuiu e quais ferramentas foram invocadas.",
      input: "Entrada", semantic: "Semântica", decision: "Decisão", agent: "Agente", output: "Saída",
    },
    visit: { visitSummary: "Resumo da visita", liveTranslator: "Tradutor ao vivo" },
  },
  vi: {
    nav: { tagline: "Điều hướng chăm sóc có hướng dẫn", home: "Trang chủ", visitAssistant: "Trợ lý thăm khám", appointments: "Lịch hẹn", notes: "Ghi chú", agentGraph: "Sơ đồ tác tử", profile: "Hồ sơ" },
    appointments: {
      badge: "Lịch hẹn", title: "Cuộc hẹn đã đặt", description: "Các cuộc hẹn đã xác nhận cho người dùng này, sắp xếp theo lần đặt gần nhất.",
      loading: "Đang tải lịch hẹn...", empty: "Chưa có lịch hẹn nào", confirmed: "Đã xác nhận", listenToRecording: "Nghe bản ghi",
      reasonForVisit: "Lý do khám", instructions: "Hướng dẫn", doctor: "Bác sĩ", location: "Địa điểm",
    },
    profile: {
      badge: "Hồ sơ", title: "Cài đặt cá nhân", description: "Các thông tin này được lưu trong hồ sơ người dùng và cache cục bộ để các cuộc trò chuyện sau nhanh hơn.",
      defaultsTitle: "Mặc định của trợ lý", defaultsDescription: "Ngôn ngữ và vị trí được áp dụng tự động cho mọi yêu cầu mới.",
      statusLoading: "Đang tải", statusSaved: "Đã lưu", statusEditing: "Đang chỉnh sửa", name: "Tên", preferredLanguage: "Ngôn ngữ ưu tiên",
      defaultLocation: "Vị trí mặc định", age: "Tuổi (tùy chọn)", gender: "Giới tính (tùy chọn)", saveProfile: "Lưu hồ sơ", saving: "Đang lưu...",
      contextTitle: "Ngữ cảnh trợ lý", contextDescription: "Hồ sơ này được áp dụng tự động trước khi trợ lý quyết định hỏi gì hoặc làm gì tiếp theo.", notSet: "Chưa đặt",
    },
    records: {
      badge: "Ghi chú đã lưu", title: "Ghi chú sau buổi khám", description: "Các ghi chú cuộc hẹn đã lưu cho người dùng này. Mở rộng thẻ để xem đầy đủ.",
      loading: "Đang tải ghi chú đã lưu...", noNotesTitle: "Chưa có ghi chú", noNotesDescription: "Tạo tóm tắt buổi khám và lưu để bắt đầu lịch sử ghi chú.",
      nothingSaved: "Chưa lưu gì", nothingSavedDescription: "Tạo tóm tắt buổi khám bằng AI và lưu với tiêu đề. Nội dung sẽ tự động xuất hiện ở đây.",
      openVisitAssistant: "Mở trợ lý thăm khám", severity: "Mức độ", expand: "Mở rộng", collapse: "Thu gọn",
    },
    graph: {
      emptyTitle: "Chưa có dữ liệu sơ đồ", emptyDescription: "Hãy chạy kiểm tra triệu chứng ở trải nghiệm chính trước. Sơ đồ tác tử sẽ xuất hiện ở đây khi backend trả về trace.",
      emptyCta: "Đi đến trải nghiệm chính", eyebrow: "Sơ đồ hệ thống", title: "Sơ đồ tác tử",
      description: "Sơ đồ này trực quan hóa hiểu ngữ nghĩa, quyết định phân nhánh, chuyên môn tác tử và việc dùng công cụ từ trace frontend hiện có.",
      panelTitle: "Sơ đồ suy luận động", panelDescription: "Ban giám khảo có thể kéo, phóng to và kiểm tra từng nhánh để xem tác tử chuyên môn nào đã đóng góp và công cụ nào được dùng.",
      input: "Đầu vào", semantic: "Ngữ nghĩa", decision: "Quyết định", agent: "Tác tử", output: "Đầu ra",
    },
    visit: { visitSummary: "Tóm tắt buổi khám", liveTranslator: "Phiên dịch trực tiếp" },
  },
  zh: {
    nav: { tagline: "引导式医疗导航", home: "首页", visitAssistant: "就诊助手", appointments: "预约", notes: "笔记", agentGraph: "智能体图谱", profile: "个人资料" },
    appointments: {
      badge: "预约", title: "已预约就诊", description: "该用户已确认的预约，按最近安排时间倒序显示。",
      loading: "正在加载预约...", empty: "还没有已安排的预约", confirmed: "已确认", listenToRecording: "收听录音",
      reasonForVisit: "就诊原因", instructions: "说明", doctor: "医生", location: "地点",
    },
    profile: {
      badge: "个人资料", title: "个人设置", description: "这些信息会保存到你的用户资料中，并缓存在本地以加快后续对话。",
      defaultsTitle: "助手默认设置", defaultsDescription: "语言和位置会自动应用到每一次新请求中。",
      statusLoading: "加载中", statusSaved: "已保存", statusEditing: "编辑中", name: "姓名", preferredLanguage: "首选语言",
      defaultLocation: "默认位置", age: "年龄（可选）", gender: "性别（可选）", saveProfile: "保存资料", saving: "保存中...",
      contextTitle: "助手上下文", contextDescription: "在助手决定下一步询问或操作之前，这份资料会自动应用。", notSet: "未设置",
    },
    records: {
      badge: "已保存笔记", title: "就诊笔记", description: "该用户保存的就诊笔记。展开卡片即可查看完整内容。",
      loading: "正在加载已保存笔记...", noNotesTitle: "还没有笔记", noNotesDescription: "先生成就诊总结并保存，开始建立你的笔记历史。",
      nothingSaved: "尚未保存任何内容", nothingSavedDescription: "从就诊助手创建 AI 总结并加上标题保存，它会自动显示在这里。",
      openVisitAssistant: "打开就诊助手", severity: "严重程度", expand: "展开", collapse: "收起",
    },
    graph: {
      emptyTitle: "暂无图谱数据", emptyDescription: "请先在主体验中运行一次症状检查。后端返回执行轨迹后，智能体图谱会显示在这里。",
      emptyCta: "前往主界面", eyebrow: "系统图谱", title: "智能体图谱",
      description: "该图谱基于现有前端轨迹，展示语义理解、分支决策、智能体分工和工具调用。",
      panelTitle: "动态推理图谱", panelDescription: "评委可以平移、缩放并检查每个分支，查看哪些专业智能体参与以及调用了哪些工具。",
      input: "输入", semantic: "语义", decision: "决策", agent: "智能体", output: "输出",
    },
    visit: { visitSummary: "就诊总结", liveTranslator: "实时翻译" },
  },
};

export function getAppCopy(language: UiLanguage): AppCopy {
  return APP_COPY[language] ?? APP_COPY.en!;
}
