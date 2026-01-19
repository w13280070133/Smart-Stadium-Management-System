import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import api from "@/utils/api";
const router = useRouter();
const loading = ref(false);
const profile = ref({
    name: "",
    mobile: "",
    status_text: "",
    balance: 0,
    level_name: "",
    level_discount: 100,
});
const stats = ref({
    totalOrders: 0,
    monthReservations: 0,
});
const recentOrders = ref([]);
const recentReservations = ref([]);
const currentMonthLabel = computed(() => {
    const d = new Date();
    return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月`;
});
const renderDiscountText = (value) => {
    if (!value || value >= 100)
        return "原价";
    const raw = value / 10;
    return `${Number.isInteger(raw) ? raw.toFixed(0) : raw.toFixed(1)} 折`;
};
/** created_at 倒序排序 */
function sortByCreatedAtDesc(list) {
    return [...list].sort((a, b) => {
        const ta = a.created_at ? new Date(a.created_at).getTime() : 0;
        const tb = b.created_at ? new Date(b.created_at).getTime() : 0;
        return tb - ta;
    });
}
function formatDate(val) {
    if (!val)
        return "-";
    if (/^\d{4}-\d{2}-\d{2}$/.test(val))
        return val;
    const d = new Date(val);
    if (Number.isNaN(d.getTime()))
        return val;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}
function formatDateTime(val) {
    if (!val)
        return "-";
    const d = new Date(val);
    if (Number.isNaN(d.getTime()))
        return val;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    return `${y}-${m}-${day} ${hh}:${mm}`;
}
/** 路由跳转 */
const goReservations = () => {
    router.push({ path: "/reservations" });
};
const goOrders = () => {
    router.push({ path: "/orders" });
};
const goProfile = () => {
    router.push({ path: "/center" });
};
const goChangePassword = () => {
    router.push({ path: "/account-settings" });
};
/** 加载个人资料 */
async function loadProfile() {
    let p = null;
    try {
        const profileRes = await api.get("/member/profile");
        p = profileRes.data;
    }
    catch {
        // 兜底：从本地读取部分信息
        p = {
            name: localStorage.getItem("member_name") ||
                localStorage.getItem("memberName") ||
                "",
            mobile: localStorage.getItem("member_phone") ||
                localStorage.getItem("memberPhone") ||
                "",
            balance: Number(localStorage.getItem("member_balance") || "0") || 0,
            status_text: "已启用",
        };
    }
    profile.value = {
        name: p.name || "",
        mobile: p.mobile || p.phone || "",
        status_text: p.status_text || p.status || "已启用",
        balance: Number(p.balance ?? 0),
    };
}
/** 概览 + 最近订单 + 最近预约 */
async function loadOverviewAndLists() {
    const [overviewRes, ordersRes, reservationsRes] = await Promise.all([
        api.get("/member/overview"),
        api.get("/member/orders", { params: { limit: 5 } }),
        api.get("/member/reservations", {
            params: { limit: 5 },
        }),
    ]);
    const overview = overviewRes.data || {};
    stats.value = {
        totalOrders: Number(overview.total_orders || 0),
        monthReservations: Number(overview.month_reservations || 0),
    };
    const orders = (ordersRes.data || []);
    const reservations = (reservationsRes.data || []);
    recentOrders.value = sortByCreatedAtDesc(orders).slice(0, 5);
    recentReservations.value = sortByCreatedAtDesc(reservations).slice(0, 5);
}
async function loadDashboard() {
    loading.value = true;
    try {
        await Promise.all([loadProfile(), loadOverviewAndLists()]);
    }
    catch (e) {
        console.error(e);
        ElMessage.error("加载首页数据失败，请稍后重试");
    }
    finally {
        loading.value = false;
    }
}
onMounted(() => {
    loadDashboard();
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['base-info']} */ ;
/** @type {__VLS_StyleScopedClasses['level-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['list-header']} */ ;
/** @type {__VLS_StyleScopedClasses['list-item']} */ ;
/** @type {__VLS_StyleScopedClasses['item-extra-right']} */ ;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "member-home" },
});
__VLS_asFunctionalDirective(__VLS_directives.vLoading)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.loading) }, null, null);
// @ts-ignore
[vLoading, loading,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "welcome-banner" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "welcome-left" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "hello" },
});
(__VLS_ctx.profile.name || "会员用户");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "tip" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "base-info" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
(__VLS_ctx.profile.mobile || "-");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "divider" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
(__VLS_ctx.profile.status_text || "已启用");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "level-badge" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
(__VLS_ctx.profile.level_name || "普通会员");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "discount" },
});
(__VLS_ctx.renderDiscountText(__VLS_ctx.profile.level_discount));
// @ts-ignore
[profile, renderDiscountText,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "action-row" },
});
const __VLS_0 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    ...{ 'onClick': {} },
    type: "primary",
    size: "small",
}));
const __VLS_2 = __VLS_1({
    ...{ 'onClick': {} },
    type: "primary",
    size: "small",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
let __VLS_4;
let __VLS_5;
const __VLS_6 = ({ click: {} },
    { onClick: (__VLS_ctx.goReservations) });
const { default: __VLS_7 } = __VLS_3.slots;
// @ts-ignore
[goReservations,];
var __VLS_3;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "welcome-right" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "balance-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "balance-value" },
});
(__VLS_ctx.profile.balance.toFixed(2));
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "balance-sub" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "quick-links" },
});
const __VLS_8 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
RouterLink;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
    to: "/center",
    ...{ class: "link-btn" },
}));
const __VLS_10 = __VLS_9({
    to: "/center",
    ...{ class: "link-btn" },
}, ...__VLS_functionalComponentArgsRest(__VLS_9));
const { default: __VLS_12 } = __VLS_11.slots;
var __VLS_11;
const __VLS_13 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
RouterLink;
// @ts-ignore
const __VLS_14 = __VLS_asFunctionalComponent(__VLS_13, new __VLS_13({
    to: "/account-settings",
    ...{ class: "link-btn" },
}));
const __VLS_15 = __VLS_14({
    to: "/account-settings",
    ...{ class: "link-btn" },
}, ...__VLS_functionalComponentArgsRest(__VLS_14));
const { default: __VLS_17 } = __VLS_16.slots;
var __VLS_16;
const __VLS_18 = {}.ElRow;
/** @type {[typeof __VLS_components.ElRow, typeof __VLS_components.elRow, typeof __VLS_components.ElRow, typeof __VLS_components.elRow, ]} */ ;
// @ts-ignore
ElRow;
// @ts-ignore
const __VLS_19 = __VLS_asFunctionalComponent(__VLS_18, new __VLS_18({
    gutter: (16),
    ...{ class: "stat-row" },
}));
const __VLS_20 = __VLS_19({
    gutter: (16),
    ...{ class: "stat-row" },
}, ...__VLS_functionalComponentArgsRest(__VLS_19));
const { default: __VLS_22 } = __VLS_21.slots;
const __VLS_23 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_24 = __VLS_asFunctionalComponent(__VLS_23, new __VLS_23({
    span: (12),
}));
const __VLS_25 = __VLS_24({
    span: (12),
}, ...__VLS_functionalComponentArgsRest(__VLS_24));
const { default: __VLS_27 } = __VLS_26.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-card stat-card-blue" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-card-top" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-badge" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-value" },
});
(__VLS_ctx.stats.totalOrders);
// @ts-ignore
[stats,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-sub" },
});
var __VLS_26;
const __VLS_28 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({
    span: (12),
}));
const __VLS_30 = __VLS_29({
    span: (12),
}, ...__VLS_functionalComponentArgsRest(__VLS_29));
const { default: __VLS_32 } = __VLS_31.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-card stat-card-purple" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-card-top" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-badge" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-value" },
});
(__VLS_ctx.stats.monthReservations);
// @ts-ignore
[stats,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-sub" },
});
(__VLS_ctx.currentMonthLabel);
// @ts-ignore
[currentMonthLabel,];
var __VLS_31;
var __VLS_21;
const __VLS_33 = {}.ElRow;
/** @type {[typeof __VLS_components.ElRow, typeof __VLS_components.elRow, typeof __VLS_components.ElRow, typeof __VLS_components.elRow, ]} */ ;
// @ts-ignore
ElRow;
// @ts-ignore
const __VLS_34 = __VLS_asFunctionalComponent(__VLS_33, new __VLS_33({
    gutter: (16),
    ...{ class: "bottom-row" },
}));
const __VLS_35 = __VLS_34({
    gutter: (16),
    ...{ class: "bottom-row" },
}, ...__VLS_functionalComponentArgsRest(__VLS_34));
const { default: __VLS_37 } = __VLS_36.slots;
const __VLS_38 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_39 = __VLS_asFunctionalComponent(__VLS_38, new __VLS_38({
    span: (12),
}));
const __VLS_40 = __VLS_39({
    span: (12),
}, ...__VLS_functionalComponentArgsRest(__VLS_39));
const { default: __VLS_42 } = __VLS_41.slots;
const __VLS_43 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_44 = __VLS_asFunctionalComponent(__VLS_43, new __VLS_43({
    shadow: "hover",
    ...{ class: "list-card" },
}));
const __VLS_45 = __VLS_44({
    shadow: "hover",
    ...{ class: "list-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_44));
const { default: __VLS_47 } = __VLS_46.slots;
{
    const { header: __VLS_48 } = __VLS_46.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "list-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "title" },
    });
    const __VLS_49 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    ElButton;
    // @ts-ignore
    const __VLS_50 = __VLS_asFunctionalComponent(__VLS_49, new __VLS_49({
        ...{ 'onClick': {} },
        type: "primary",
        text: true,
        size: "small",
    }));
    const __VLS_51 = __VLS_50({
        ...{ 'onClick': {} },
        type: "primary",
        text: true,
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_50));
    let __VLS_53;
    let __VLS_54;
    const __VLS_55 = ({ click: {} },
        { onClick: (__VLS_ctx.goReservations) });
    const { default: __VLS_56 } = __VLS_52.slots;
    // @ts-ignore
    [goReservations,];
    var __VLS_52;
}
if (!__VLS_ctx.recentReservations.length) {
    // @ts-ignore
    [recentReservations,];
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "empty-wrapper" },
    });
    const __VLS_57 = {}.ElEmpty;
    /** @type {[typeof __VLS_components.ElEmpty, typeof __VLS_components.elEmpty, ]} */ ;
    // @ts-ignore
    ElEmpty;
    // @ts-ignore
    const __VLS_58 = __VLS_asFunctionalComponent(__VLS_57, new __VLS_57({
        description: "暂无预约记录",
    }));
    const __VLS_59 = __VLS_58({
        description: "暂无预约记录",
    }, ...__VLS_functionalComponentArgsRest(__VLS_58));
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "list-body" },
    });
    for (const [item] of __VLS_getVForSourceType((__VLS_ctx.recentReservations))) {
        // @ts-ignore
        [recentReservations,];
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            key: (item.id),
            ...{ class: "list-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-main" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-title" },
        });
        (item.court_name || "未知场地");
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-time" },
        });
        (__VLS_ctx.formatDate(item.date));
        (item.start_time);
        (item.end_time);
        // @ts-ignore
        [formatDate,];
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-extra" },
        });
        const __VLS_62 = {}.ElTag;
        /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
        // @ts-ignore
        ElTag;
        // @ts-ignore
        const __VLS_63 = __VLS_asFunctionalComponent(__VLS_62, new __VLS_62({
            size: "small",
        }));
        const __VLS_64 = __VLS_63({
            size: "small",
        }, ...__VLS_functionalComponentArgsRest(__VLS_63));
        const { default: __VLS_66 } = __VLS_65.slots;
        (item.status || "-");
        var __VLS_65;
    }
}
var __VLS_46;
var __VLS_41;
const __VLS_67 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_68 = __VLS_asFunctionalComponent(__VLS_67, new __VLS_67({
    span: (12),
}));
const __VLS_69 = __VLS_68({
    span: (12),
}, ...__VLS_functionalComponentArgsRest(__VLS_68));
const { default: __VLS_71 } = __VLS_70.slots;
const __VLS_72 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_73 = __VLS_asFunctionalComponent(__VLS_72, new __VLS_72({
    shadow: "hover",
    ...{ class: "list-card" },
}));
const __VLS_74 = __VLS_73({
    shadow: "hover",
    ...{ class: "list-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_73));
const { default: __VLS_76 } = __VLS_75.slots;
{
    const { header: __VLS_77 } = __VLS_75.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "list-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "title" },
    });
    const __VLS_78 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    ElButton;
    // @ts-ignore
    const __VLS_79 = __VLS_asFunctionalComponent(__VLS_78, new __VLS_78({
        ...{ 'onClick': {} },
        type: "primary",
        text: true,
        size: "small",
    }));
    const __VLS_80 = __VLS_79({
        ...{ 'onClick': {} },
        type: "primary",
        text: true,
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_79));
    let __VLS_82;
    let __VLS_83;
    const __VLS_84 = ({ click: {} },
        { onClick: (__VLS_ctx.goOrders) });
    const { default: __VLS_85 } = __VLS_81.slots;
    // @ts-ignore
    [goOrders,];
    var __VLS_81;
}
if (!__VLS_ctx.recentOrders.length) {
    // @ts-ignore
    [recentOrders,];
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "empty-wrapper" },
    });
    const __VLS_86 = {}.ElEmpty;
    /** @type {[typeof __VLS_components.ElEmpty, typeof __VLS_components.elEmpty, ]} */ ;
    // @ts-ignore
    ElEmpty;
    // @ts-ignore
    const __VLS_87 = __VLS_asFunctionalComponent(__VLS_86, new __VLS_86({
        description: "暂无订单记录",
    }));
    const __VLS_88 = __VLS_87({
        description: "暂无订单记录",
    }, ...__VLS_functionalComponentArgsRest(__VLS_87));
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "list-body" },
    });
    for (const [order] of __VLS_getVForSourceType((__VLS_ctx.recentOrders))) {
        // @ts-ignore
        [recentOrders,];
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            key: (order.id),
            ...{ class: "list-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-main" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-title" },
        });
        (order.type || order.order_no || "订单");
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-time" },
        });
        (__VLS_ctx.formatDateTime(order.created_at));
        // @ts-ignore
        [formatDateTime,];
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-extra item-extra-right" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "amount" },
        });
        (Number(order.amount || 0).toFixed(2));
        const __VLS_91 = {}.ElTag;
        /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
        // @ts-ignore
        ElTag;
        // @ts-ignore
        const __VLS_92 = __VLS_asFunctionalComponent(__VLS_91, new __VLS_91({
            size: "small",
        }));
        const __VLS_93 = __VLS_92({
            size: "small",
        }, ...__VLS_functionalComponentArgsRest(__VLS_92));
        const { default: __VLS_95 } = __VLS_94.slots;
        (order.status || "-");
        var __VLS_94;
    }
}
var __VLS_75;
var __VLS_70;
var __VLS_36;
/** @type {__VLS_StyleScopedClasses['member-home']} */ ;
/** @type {__VLS_StyleScopedClasses['welcome-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['welcome-left']} */ ;
/** @type {__VLS_StyleScopedClasses['hello']} */ ;
/** @type {__VLS_StyleScopedClasses['tip']} */ ;
/** @type {__VLS_StyleScopedClasses['base-info']} */ ;
/** @type {__VLS_StyleScopedClasses['divider']} */ ;
/** @type {__VLS_StyleScopedClasses['level-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['discount']} */ ;
/** @type {__VLS_StyleScopedClasses['action-row']} */ ;
/** @type {__VLS_StyleScopedClasses['welcome-right']} */ ;
/** @type {__VLS_StyleScopedClasses['balance-label']} */ ;
/** @type {__VLS_StyleScopedClasses['balance-value']} */ ;
/** @type {__VLS_StyleScopedClasses['balance-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['quick-links']} */ ;
/** @type {__VLS_StyleScopedClasses['link-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['link-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-row']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card-blue']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card-top']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-title']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-value']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card-purple']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card-top']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-title']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-value']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['bottom-row']} */ ;
/** @type {__VLS_StyleScopedClasses['list-card']} */ ;
/** @type {__VLS_StyleScopedClasses['list-header']} */ ;
/** @type {__VLS_StyleScopedClasses['title']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['list-body']} */ ;
/** @type {__VLS_StyleScopedClasses['list-item']} */ ;
/** @type {__VLS_StyleScopedClasses['item-main']} */ ;
/** @type {__VLS_StyleScopedClasses['item-title']} */ ;
/** @type {__VLS_StyleScopedClasses['item-time']} */ ;
/** @type {__VLS_StyleScopedClasses['item-extra']} */ ;
/** @type {__VLS_StyleScopedClasses['list-card']} */ ;
/** @type {__VLS_StyleScopedClasses['list-header']} */ ;
/** @type {__VLS_StyleScopedClasses['title']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['list-body']} */ ;
/** @type {__VLS_StyleScopedClasses['list-item']} */ ;
/** @type {__VLS_StyleScopedClasses['item-main']} */ ;
/** @type {__VLS_StyleScopedClasses['item-title']} */ ;
/** @type {__VLS_StyleScopedClasses['item-time']} */ ;
/** @type {__VLS_StyleScopedClasses['item-extra']} */ ;
/** @type {__VLS_StyleScopedClasses['item-extra-right']} */ ;
/** @type {__VLS_StyleScopedClasses['amount']} */ ;
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
