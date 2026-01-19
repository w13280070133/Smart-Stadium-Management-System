import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import api from "@/utils/api";
const orders = ref([]);
const loading = ref(false);
function renderStatus(status) {
    const s = (status || "").toLowerCase();
    switch (s) {
        case "paid":
        case "已支付":
            return "已支付";
        case "unpaid":
        case "pending":
        case "未支付":
            return "未支付";
        case "cancelled":
        case "canceled":
        case "已取消":
            return "已取消";
        case "refunded":
        case "已退款":
            return "已退款";
        case "partial_refund":
            return "部分退款";
        default:
            return status || "-";
    }
}
function statusTagType(status) {
    const s = (status || "").toLowerCase();
    if (s === "paid")
        return "success";
    if (s === "unpaid" || s === "pending")
        return "info";
    if (s === "refunded" || s === "partial_refund")
        return "warning";
    if (s === "cancelled" || s === "canceled")
        return "danger";
    return "";
}
async function loadOrders() {
    loading.value = true;
    try {
        const res = await api.get("/member/orders");
        orders.value = res.data || [];
    }
    catch (e) {
        console.error(e);
        ElMessage.error(e?.response?.data?.detail || "获取订单失败");
    }
    finally {
        loading.value = false;
    }
}
onMounted(() => {
    loadOrders();
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-header" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-header-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-header-subtitle" },
});
const __VLS_0 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    shadow: "hover",
    ...{ class: "page-card" },
}));
const __VLS_2 = __VLS_1({
    shadow: "hover",
    ...{ class: "page-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
const { default: __VLS_4 } = __VLS_3.slots;
const __VLS_5 = {}.ElTable;
/** @type {[typeof __VLS_components.ElTable, typeof __VLS_components.elTable, typeof __VLS_components.ElTable, typeof __VLS_components.elTable, ]} */ ;
// @ts-ignore
ElTable;
// @ts-ignore
const __VLS_6 = __VLS_asFunctionalComponent(__VLS_5, new __VLS_5({
    data: (__VLS_ctx.orders),
    border: true,
    ...{ style: {} },
}));
const __VLS_7 = __VLS_6({
    data: (__VLS_ctx.orders),
    border: true,
    ...{ style: {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_6));
__VLS_asFunctionalDirective(__VLS_directives.vLoading)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.loading) }, null, null);
const { default: __VLS_9 } = __VLS_8.slots;
// @ts-ignore
[orders, vLoading, loading,];
const __VLS_10 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_11 = __VLS_asFunctionalComponent(__VLS_10, new __VLS_10({
    prop: "order_no",
    label: "订单号",
    width: "180",
}));
const __VLS_12 = __VLS_11({
    prop: "order_no",
    label: "订单号",
    width: "180",
}, ...__VLS_functionalComponentArgsRest(__VLS_11));
const __VLS_15 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_16 = __VLS_asFunctionalComponent(__VLS_15, new __VLS_15({
    prop: "type",
    label: "业务类型",
    width: "120",
}));
const __VLS_17 = __VLS_16({
    prop: "type",
    label: "业务类型",
    width: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_16));
const __VLS_20 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({
    label: "金额(元)",
    width: "120",
}));
const __VLS_22 = __VLS_21({
    label: "金额(元)",
    width: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_21));
const { default: __VLS_24 } = __VLS_23.slots;
{
    const { default: __VLS_25 } = __VLS_23.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_25);
    (Number(row.amount || 0).toFixed(2));
}
var __VLS_23;
const __VLS_26 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_27 = __VLS_asFunctionalComponent(__VLS_26, new __VLS_26({
    prop: "status",
    label: "订单状态",
    width: "110",
}));
const __VLS_28 = __VLS_27({
    prop: "status",
    label: "订单状态",
    width: "110",
}, ...__VLS_functionalComponentArgsRest(__VLS_27));
const { default: __VLS_30 } = __VLS_29.slots;
{
    const { default: __VLS_31 } = __VLS_29.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_31);
    const __VLS_32 = {}.ElTag;
    /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
    // @ts-ignore
    ElTag;
    // @ts-ignore
    const __VLS_33 = __VLS_asFunctionalComponent(__VLS_32, new __VLS_32({
        type: (__VLS_ctx.statusTagType(row.status)),
        size: "small",
    }));
    const __VLS_34 = __VLS_33({
        type: (__VLS_ctx.statusTagType(row.status)),
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_33));
    const { default: __VLS_36 } = __VLS_35.slots;
    // @ts-ignore
    [statusTagType,];
    (__VLS_ctx.renderStatus(row.status));
    // @ts-ignore
    [renderStatus,];
    var __VLS_35;
}
var __VLS_29;
const __VLS_37 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_38 = __VLS_asFunctionalComponent(__VLS_37, new __VLS_37({
    prop: "created_at",
    label: "创建时间",
    width: "180",
}));
const __VLS_39 = __VLS_38({
    prop: "created_at",
    label: "创建时间",
    width: "180",
}, ...__VLS_functionalComponentArgsRest(__VLS_38));
var __VLS_8;
if (!__VLS_ctx.loading && __VLS_ctx.orders.length === 0) {
    // @ts-ignore
    [orders, loading,];
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "empty" },
    });
}
var __VLS_3;
/** @type {__VLS_StyleScopedClasses['page']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header-title']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header-subtitle']} */ ;
/** @type {__VLS_StyleScopedClasses['page-card']} */ ;
/** @type {__VLS_StyleScopedClasses['empty']} */ ;
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
