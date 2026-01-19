import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import api from "@/utils/api";
const loading = ref(false);
const orders = ref([]);
const filters = ref({
    type: "",
    status: "",
    keyword: "",
});
const totalCount = computed(() => orders.value.length);
const courtCount = computed(() => orders.value.filter((o) => normalizeType(o.order_type) === "court").length);
const goodsCount = computed(() => orders.value.filter((o) => normalizeType(o.order_type) === "goods").length);
const refundCount = computed(() => orders.value.filter((o) => normalizeType(o.order_type) === "refund").length);
const filteredOrders = computed(() => {
    return orders.value.filter((o) => {
        const t = normalizeType(o.order_type);
        const s = (o.status || "").toString().toLowerCase();
        if (filters.value.type && t !== filters.value.type)
            return false;
        if (filters.value.status) {
            const fs = filters.value.status.toLowerCase();
            if (s !== fs)
                return false;
        }
        if (filters.value.keyword) {
            const kw = filters.value.keyword.trim();
            if (!(o.order_no || "").includes(kw) && !(renderType(o.order_type)).includes(kw)) {
                return false;
            }
        }
        return true;
    });
});
function normalizeType(type) {
    const t = (type || "").toLowerCase();
    if (t === "product")
        return "goods";
    return t;
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
function renderType(t) {
    const nt = normalizeType(t);
    if (nt === "court")
        return "场地预约";
    if (nt === "goods")
        return "商品消费";
    if (nt === "refund")
        return "退款";
    return "其他";
}
function renderStatus(status) {
    const s = (status || "").toLowerCase();
    if (s === "paid")
        return "已支付";
    if (s === "pending")
        return "未支付";
    if (s === "refunded")
        return "已退款";
    if (s === "partial_refund")
        return "部分退款";
    if (s === "closed")
        return "已关闭";
    return status || "-";
}
function statusTagType(status) {
    const s = (status || "").toLowerCase();
    if (s === "paid")
        return "success";
    if (s === "refunded" || s === "partial_refund")
        return "warning";
    if (s === "pending")
        return "info";
    if (s === "closed")
        return "danger";
    return "";
}
function resetFilter() {
    filters.value.type = "";
    filters.value.status = "";
    filters.value.keyword = "";
}
const loadOrders = async () => {
    loading.value = true;
    try {
        const res = await api.get("/member/orders", { params: { limit: 100 } });
        orders.value = res.data || [];
    }
    catch (err) {
        ElMessage.error(err?.response?.data?.detail || "获取订单失败");
    }
    finally {
        loading.value = false;
    }
};
onMounted(loadOrders);
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['stat-card']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card']} */ ;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "orders-page" },
});
__VLS_asFunctionalDirective(__VLS_directives.vLoading)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.loading) }, null, null);
// @ts-ignore
[vLoading, loading,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-header" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "sub-title" },
});
const __VLS_0 = {}.ElRow;
/** @type {[typeof __VLS_components.ElRow, typeof __VLS_components.elRow, typeof __VLS_components.ElRow, typeof __VLS_components.elRow, ]} */ ;
// @ts-ignore
ElRow;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    gutter: (12),
    ...{ class: "stat-row" },
}));
const __VLS_2 = __VLS_1({
    gutter: (12),
    ...{ class: "stat-row" },
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
const { default: __VLS_4 } = __VLS_3.slots;
const __VLS_5 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_6 = __VLS_asFunctionalComponent(__VLS_5, new __VLS_5({
    span: (6),
}));
const __VLS_7 = __VLS_6({
    span: (6),
}, ...__VLS_functionalComponentArgsRest(__VLS_6));
const { default: __VLS_9 } = __VLS_8.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "value" },
});
(__VLS_ctx.totalCount);
// @ts-ignore
[totalCount,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "desc" },
});
var __VLS_8;
const __VLS_10 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_11 = __VLS_asFunctionalComponent(__VLS_10, new __VLS_10({
    span: (6),
}));
const __VLS_12 = __VLS_11({
    span: (6),
}, ...__VLS_functionalComponentArgsRest(__VLS_11));
const { default: __VLS_14 } = __VLS_13.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-card stat-court" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "value" },
});
(__VLS_ctx.courtCount);
// @ts-ignore
[courtCount,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "desc" },
});
var __VLS_13;
const __VLS_15 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_16 = __VLS_asFunctionalComponent(__VLS_15, new __VLS_15({
    span: (6),
}));
const __VLS_17 = __VLS_16({
    span: (6),
}, ...__VLS_functionalComponentArgsRest(__VLS_16));
const { default: __VLS_19 } = __VLS_18.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-card stat-goods" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "value" },
});
(__VLS_ctx.goodsCount);
// @ts-ignore
[goodsCount,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "desc" },
});
var __VLS_18;
const __VLS_20 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({
    span: (6),
}));
const __VLS_22 = __VLS_21({
    span: (6),
}, ...__VLS_functionalComponentArgsRest(__VLS_21));
const { default: __VLS_24 } = __VLS_23.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-card stat-refund" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "value" },
});
(__VLS_ctx.refundCount);
// @ts-ignore
[refundCount,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "desc" },
});
var __VLS_23;
var __VLS_3;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "filter-bar" },
});
const __VLS_25 = {}.ElSelect;
/** @type {[typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, ]} */ ;
// @ts-ignore
ElSelect;
// @ts-ignore
const __VLS_26 = __VLS_asFunctionalComponent(__VLS_25, new __VLS_25({
    modelValue: (__VLS_ctx.filters.type),
    placeholder: "全部类型",
    clearable: true,
    ...{ style: {} },
    size: "small",
}));
const __VLS_27 = __VLS_26({
    modelValue: (__VLS_ctx.filters.type),
    placeholder: "全部类型",
    clearable: true,
    ...{ style: {} },
    size: "small",
}, ...__VLS_functionalComponentArgsRest(__VLS_26));
const { default: __VLS_29 } = __VLS_28.slots;
// @ts-ignore
[filters,];
const __VLS_30 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_31 = __VLS_asFunctionalComponent(__VLS_30, new __VLS_30({
    label: "场地预约",
    value: "court",
}));
const __VLS_32 = __VLS_31({
    label: "场地预约",
    value: "court",
}, ...__VLS_functionalComponentArgsRest(__VLS_31));
const __VLS_35 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_36 = __VLS_asFunctionalComponent(__VLS_35, new __VLS_35({
    label: "商品消费",
    value: "goods",
}));
const __VLS_37 = __VLS_36({
    label: "商品消费",
    value: "goods",
}, ...__VLS_functionalComponentArgsRest(__VLS_36));
const __VLS_40 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_41 = __VLS_asFunctionalComponent(__VLS_40, new __VLS_40({
    label: "退款",
    value: "refund",
}));
const __VLS_42 = __VLS_41({
    label: "退款",
    value: "refund",
}, ...__VLS_functionalComponentArgsRest(__VLS_41));
var __VLS_28;
const __VLS_45 = {}.ElSelect;
/** @type {[typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, ]} */ ;
// @ts-ignore
ElSelect;
// @ts-ignore
const __VLS_46 = __VLS_asFunctionalComponent(__VLS_45, new __VLS_45({
    modelValue: (__VLS_ctx.filters.status),
    placeholder: "全部状态",
    clearable: true,
    ...{ style: {} },
    size: "small",
}));
const __VLS_47 = __VLS_46({
    modelValue: (__VLS_ctx.filters.status),
    placeholder: "全部状态",
    clearable: true,
    ...{ style: {} },
    size: "small",
}, ...__VLS_functionalComponentArgsRest(__VLS_46));
const { default: __VLS_49 } = __VLS_48.slots;
// @ts-ignore
[filters,];
const __VLS_50 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_51 = __VLS_asFunctionalComponent(__VLS_50, new __VLS_50({
    label: "已支付",
    value: "paid",
}));
const __VLS_52 = __VLS_51({
    label: "已支付",
    value: "paid",
}, ...__VLS_functionalComponentArgsRest(__VLS_51));
const __VLS_55 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_56 = __VLS_asFunctionalComponent(__VLS_55, new __VLS_55({
    label: "未支付",
    value: "pending",
}));
const __VLS_57 = __VLS_56({
    label: "未支付",
    value: "pending",
}, ...__VLS_functionalComponentArgsRest(__VLS_56));
const __VLS_60 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_61 = __VLS_asFunctionalComponent(__VLS_60, new __VLS_60({
    label: "已退款",
    value: "refunded",
}));
const __VLS_62 = __VLS_61({
    label: "已退款",
    value: "refunded",
}, ...__VLS_functionalComponentArgsRest(__VLS_61));
const __VLS_65 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_66 = __VLS_asFunctionalComponent(__VLS_65, new __VLS_65({
    label: "部分退款",
    value: "partial_refund",
}));
const __VLS_67 = __VLS_66({
    label: "部分退款",
    value: "partial_refund",
}, ...__VLS_functionalComponentArgsRest(__VLS_66));
const __VLS_70 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_71 = __VLS_asFunctionalComponent(__VLS_70, new __VLS_70({
    label: "已关闭",
    value: "closed",
}));
const __VLS_72 = __VLS_71({
    label: "已关闭",
    value: "closed",
}, ...__VLS_functionalComponentArgsRest(__VLS_71));
var __VLS_48;
const __VLS_75 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
ElInput;
// @ts-ignore
const __VLS_76 = __VLS_asFunctionalComponent(__VLS_75, new __VLS_75({
    modelValue: (__VLS_ctx.filters.keyword),
    placeholder: "按订单号 / 类型搜索",
    size: "small",
    clearable: true,
    ...{ style: {} },
}));
const __VLS_77 = __VLS_76({
    modelValue: (__VLS_ctx.filters.keyword),
    placeholder: "按订单号 / 类型搜索",
    size: "small",
    clearable: true,
    ...{ style: {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_76));
const { default: __VLS_79 } = __VLS_78.slots;
// @ts-ignore
[filters,];
{
    const { prefix: __VLS_80 } = __VLS_78.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.i)({
        ...{ class: "el-icon-search" },
    });
}
var __VLS_78;
const __VLS_81 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_82 = __VLS_asFunctionalComponent(__VLS_81, new __VLS_81({
    ...{ 'onClick': {} },
    size: "small",
    type: "primary",
    text: true,
    ...{ style: {} },
}));
const __VLS_83 = __VLS_82({
    ...{ 'onClick': {} },
    size: "small",
    type: "primary",
    text: true,
    ...{ style: {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_82));
let __VLS_85;
let __VLS_86;
const __VLS_87 = ({ click: {} },
    { onClick: (__VLS_ctx.resetFilter) });
const { default: __VLS_88 } = __VLS_84.slots;
// @ts-ignore
[resetFilter,];
var __VLS_84;
const __VLS_89 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_90 = __VLS_asFunctionalComponent(__VLS_89, new __VLS_89({
    shadow: "hover",
    ...{ class: "table-card" },
}));
const __VLS_91 = __VLS_90({
    shadow: "hover",
    ...{ class: "table-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_90));
const { default: __VLS_93 } = __VLS_92.slots;
const __VLS_94 = {}.ElTable;
/** @type {[typeof __VLS_components.ElTable, typeof __VLS_components.elTable, typeof __VLS_components.ElTable, typeof __VLS_components.elTable, ]} */ ;
// @ts-ignore
ElTable;
// @ts-ignore
const __VLS_95 = __VLS_asFunctionalComponent(__VLS_94, new __VLS_94({
    data: (__VLS_ctx.filteredOrders),
    ...{ style: {} },
    border: true,
    size: "small",
}));
const __VLS_96 = __VLS_95({
    data: (__VLS_ctx.filteredOrders),
    ...{ style: {} },
    border: true,
    size: "small",
}, ...__VLS_functionalComponentArgsRest(__VLS_95));
const { default: __VLS_98 } = __VLS_97.slots;
// @ts-ignore
[filteredOrders,];
const __VLS_99 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_100 = __VLS_asFunctionalComponent(__VLS_99, new __VLS_99({
    prop: "order_no",
    label: "订单号",
    minWidth: "160",
    showOverflowTooltip: true,
}));
const __VLS_101 = __VLS_100({
    prop: "order_no",
    label: "订单号",
    minWidth: "160",
    showOverflowTooltip: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_100));
const __VLS_104 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_105 = __VLS_asFunctionalComponent(__VLS_104, new __VLS_104({
    prop: "order_type",
    label: "类型",
    width: "110",
}));
const __VLS_106 = __VLS_105({
    prop: "order_type",
    label: "类型",
    width: "110",
}, ...__VLS_functionalComponentArgsRest(__VLS_105));
const { default: __VLS_108 } = __VLS_107.slots;
{
    const { default: __VLS_109 } = __VLS_107.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_109);
    (__VLS_ctx.renderType(row.order_type));
    // @ts-ignore
    [renderType,];
}
var __VLS_107;
const __VLS_110 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_111 = __VLS_asFunctionalComponent(__VLS_110, new __VLS_110({
    prop: "pay_amount",
    label: "金额（元）",
    width: "120",
}));
const __VLS_112 = __VLS_111({
    prop: "pay_amount",
    label: "金额（元）",
    width: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_111));
const { default: __VLS_114 } = __VLS_113.slots;
{
    const { default: __VLS_115 } = __VLS_113.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_115);
    (Number(row.pay_amount ?? row.total_amount ?? 0).toFixed(2));
}
var __VLS_113;
const __VLS_116 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_117 = __VLS_asFunctionalComponent(__VLS_116, new __VLS_116({
    prop: "status",
    label: "状态",
    width: "120",
}));
const __VLS_118 = __VLS_117({
    prop: "status",
    label: "状态",
    width: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_117));
const { default: __VLS_120 } = __VLS_119.slots;
{
    const { default: __VLS_121 } = __VLS_119.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_121);
    const __VLS_122 = {}.ElTag;
    /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
    // @ts-ignore
    ElTag;
    // @ts-ignore
    const __VLS_123 = __VLS_asFunctionalComponent(__VLS_122, new __VLS_122({
        size: "small",
        type: (__VLS_ctx.statusTagType(row.status)),
    }));
    const __VLS_124 = __VLS_123({
        size: "small",
        type: (__VLS_ctx.statusTagType(row.status)),
    }, ...__VLS_functionalComponentArgsRest(__VLS_123));
    const { default: __VLS_126 } = __VLS_125.slots;
    // @ts-ignore
    [statusTagType,];
    (__VLS_ctx.renderStatus(row.status));
    // @ts-ignore
    [renderStatus,];
    var __VLS_125;
}
var __VLS_119;
const __VLS_127 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_128 = __VLS_asFunctionalComponent(__VLS_127, new __VLS_127({
    prop: "created_at",
    label: "下单时间",
    minWidth: "160",
}));
const __VLS_129 = __VLS_128({
    prop: "created_at",
    label: "下单时间",
    minWidth: "160",
}, ...__VLS_functionalComponentArgsRest(__VLS_128));
const { default: __VLS_131 } = __VLS_130.slots;
{
    const { default: __VLS_132 } = __VLS_130.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_132);
    (__VLS_ctx.formatDateTime(row.created_at));
    // @ts-ignore
    [formatDateTime,];
}
var __VLS_130;
var __VLS_97;
if (!__VLS_ctx.filteredOrders.length && !__VLS_ctx.loading) {
    // @ts-ignore
    [loading, filteredOrders,];
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "empty-wrapper" },
    });
    const __VLS_133 = {}.ElEmpty;
    /** @type {[typeof __VLS_components.ElEmpty, typeof __VLS_components.elEmpty, ]} */ ;
    // @ts-ignore
    ElEmpty;
    // @ts-ignore
    const __VLS_134 = __VLS_asFunctionalComponent(__VLS_133, new __VLS_133({
        description: "暂无订单记录",
    }));
    const __VLS_135 = __VLS_134({
        description: "暂无订单记录",
    }, ...__VLS_functionalComponentArgsRest(__VLS_134));
}
var __VLS_92;
/** @type {__VLS_StyleScopedClasses['orders-page']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-title']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-row']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['desc']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-court']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['desc']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-goods']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['desc']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-card']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-refund']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['desc']} */ ;
/** @type {__VLS_StyleScopedClasses['filter-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['el-icon-search']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-wrapper']} */ ;
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
